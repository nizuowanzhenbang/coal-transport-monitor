"""仪表盘API：概览数据、趋势分析、排名统计"""
from datetime import datetime, timedelta, timezone

import numpy as np
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.transport import TransportRecord, RecordStatus
from app.models.alert import Alert, AlertType, Severity
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.dashboard import OverviewData, AlertTrendItem, TopRiskVehicle, WeightDistributionItem
from app.utils.helpers import api_response

router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取仪表盘概览数据（KPI卡片）

    返回：总运输数、今日运输、待处理预警、严重预警、异常率、平均时长、车辆数
    """
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

    total_transports = db.query(func.count(TransportRecord.id)).scalar() or 0
    today_transports = (
        db.query(func.count(TransportRecord.id))
        .filter(TransportRecord.created_at >= today_start)
        .scalar() or 0
    )
    pending_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.status == "PENDING")
        .scalar() or 0
    )
    severe_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.severity == Severity.SEVERE, Alert.status == "PENDING")
        .scalar() or 0
    )

    # 异常率：有预警的运输记录 / 总运输记录
    abnormal_transports = (
        db.query(func.count(func.distinct(Alert.transport_id))).scalar() or 0
    )
    anomaly_rate = abnormal_transports / total_transports if total_transports > 0 else 0.0

    # 平均运输时长
    avg_duration = (
        db.query(func.avg(TransportRecord.transport_duration))
        .filter(TransportRecord.transport_duration.isnot(None))
        .scalar() or 0
    )

    total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0
    active_vehicles = (
        db.query(func.count(Vehicle.id))
        .filter(Vehicle.status == VehicleStatus.ACTIVE)
        .scalar() or 0
    )

    data = OverviewData(
        total_transports=total_transports,
        today_transports=today_transports,
        pending_alerts=pending_alerts,
        severe_alerts=severe_alerts,
        anomaly_rate=round(anomaly_rate, 4),
        avg_duration_minutes=int(avg_duration),
        total_vehicles=total_vehicles,
        active_vehicles=active_vehicles,
    )

    return api_response(data=data.model_dump())


@router.get("/alert-trend")
def get_alert_trend(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取预警趋势数据（按日统计）"""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    # 按日分组统计各类预警
    results = (
        db.query(
            func.date(Alert.created_at).label("date"),
            func.count(Alert.id).label("total"),
            func.sum(case(
                (Alert.alert_type.in_([AlertType.WEIGHT_SHORTAGE, AlertType.WEIGHT_OVERAGE]), 1),
                else_=0,
            )).label("weight_count"),
            func.sum(case(
                (Alert.alert_type == AlertType.TIME_EXCESSIVE, 1),
                else_=0,
            )).label("time_count"),
            func.sum(case(
                (Alert.alert_type.in_([AlertType.SEAL_MISMATCH, AlertType.SEAL_DAMAGED]), 1),
                else_=0,
            )).label("seal_count"),
        )
        .filter(Alert.created_at >= cutoff)
        .group_by(func.date(Alert.created_at))
        .order_by(func.date(Alert.created_at))
        .all()
    )

    items = [
        AlertTrendItem(
            date=str(r.date),
            total=r.total,
            weight_count=r.weight_count or 0,
            time_count=r.time_count or 0,
            seal_count=r.seal_count or 0,
        ).model_dump()
        for r in results
    ]

    return api_response(data=items)


@router.get("/top-risk-vehicles")
def get_top_risk_vehicles(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取高风险车辆TOP N"""
    # 统计每辆车的严重预警次数
    results = (
        db.query(
            Vehicle.plate_number,
            func.count(Alert.id).label("total_alerts"),
            func.sum(case((Alert.severity == Severity.SEVERE, 1), else_=0)).label("severe_count"),
            func.max(Alert.created_at).label("last_alert_time"),
        )
        .join(TransportRecord, TransportRecord.vehicle_id == Vehicle.id)
        .join(Alert, Alert.transport_id == TransportRecord.id)
        .group_by(Vehicle.id, Vehicle.plate_number)
        .order_by(func.count(Alert.id).desc())
        .limit(limit)
        .all()
    )

    items = [
        TopRiskVehicle(
            plate_number=r.plate_number,
            total_alerts=r.total_alerts,
            severe_count=r.severe_count or 0,
            last_alert_time=str(r.last_alert_time) if r.last_alert_time else None,
        ).model_dump()
        for r in results
    ]

    return api_response(data=items)


@router.get("/weight-distribution")
def get_weight_distribution(
    bins: int = Query(10, ge=5, le=20),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取重量偏差分布数据（直方图）"""
    # 获取所有有效偏差率
    ratios = (
        db.query(TransportRecord.weight_diff_ratio)
        .filter(TransportRecord.weight_diff_ratio.isnot(None))
        .all()
    )
    ratios = [r[0] for r in ratios if r[0] is not None]

    if not ratios:
        return api_response(data=[])

    # 使用 numpy.histogram 替代 O(n*m) Python 循环
    arr = np.array(ratios, dtype=float)
    counts, edges = np.histogram(arr, bins=bins)
    distribution = [
        WeightDistributionItem(
            range_min=round(float(edges[i]), 6),
            range_max=round(float(edges[i + 1]), 6),
            count=int(counts[i]),
        ).model_dump()
        for i in range(len(counts))
    ]

    return api_response(data=distribution)
