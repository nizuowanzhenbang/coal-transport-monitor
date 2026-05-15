"""数据导出API：CSV/Excel格式导出运输记录和预警数据"""
import csv
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.models.alert import Alert, AlertType, AlertStatus, Severity
from app.models.transport import TransportRecord, RecordStatus
from app.models.vehicle import Vehicle

router = APIRouter(prefix="/api/export", tags=["数据导出"])

_STATUS_LABELS = {
    RecordStatus.NORMAL: "正常",
    RecordStatus.ALERT: "一般预警",
    RecordStatus.SEVERE: "严重预警",
}
_ALERT_TYPE_LABELS = {
    AlertType.WEIGHT_SHORTAGE: "亏吨",
    AlertType.WEIGHT_OVERAGE: "盈吨",
    AlertType.TIME_EXCESSIVE: "运输超时",
    AlertType.SEAL_MISMATCH: "铅封不一致",
    AlertType.SEAL_DAMAGED: "铅封损坏",
}
_SEVERITY_LABELS = {Severity.GENERAL: "一般", Severity.SEVERE: "严重"}
_ALERT_STATUS_LABELS = {
    AlertStatus.PENDING: "待处理",
    AlertStatus.ACKNOWLEDGED: "已确认",
    AlertStatus.RESOLVED: "已解决",
    AlertStatus.DISMISSED: "已忽略",
}


def _fmt_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _fmt_float(v: Optional[float], precision: int = 2) -> str:
    if v is None:
        return ""
    return f"{v:.{precision}f}"


@router.get("/transports")
def export_transports(
    status: Optional[RecordStatus] = Query(None, description="状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    plate: Optional[str] = Query(None, description="车牌号筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """导出运输记录为 CSV（支持与列表相同的筛选条件）"""
    query = db.query(TransportRecord).options(joinedload(TransportRecord.vehicle))

    if status:
        query = query.filter(TransportRecord.status == status)
    if start_date:
        query = query.filter(TransportRecord.departure_time >= start_date)
    if end_date:
        query = query.filter(TransportRecord.arrival_time <= end_date)
    if plate:
        query = query.join(Vehicle, Vehicle.id == TransportRecord.vehicle_id).filter(
            Vehicle.plate_number.contains(plate)
        )

    records = query.order_by(TransportRecord.departure_time.desc()).all()

    output = io.StringIO()
    output.write("﻿")  # UTF-8 BOM，让 Excel 正确识别中文
    writer = csv.writer(output)
    writer.writerow([
        "记录ID", "车牌号", "出发港口",
        "出港时间", "到达时间",
        "出港毛重(t)", "出港净重(t)",
        "进厂毛重(t)", "进厂净重(t)",
        "重量差(t)", "偏差率(‰)",
        "运输时长(分钟)", "状态", "预警次数", "备注",
    ])
    for r in records:
        plate_no = r.vehicle.plate_number if r.vehicle else ""
        ratio_permille = f"{r.weight_diff_ratio * 1000:.2f}" if r.weight_diff_ratio is not None else ""
        writer.writerow([
            r.id,
            plate_no,
            r.departure_port or "",
            _fmt_dt(r.departure_time),
            _fmt_dt(r.arrival_time),
            _fmt_float(r.departure_weight / 1000 if r.departure_weight else None, 3),
            _fmt_float(r.departure_net_weight / 1000 if r.departure_net_weight else None, 3),
            _fmt_float(r.arrival_weight / 1000 if r.arrival_weight else None, 3),
            _fmt_float(r.arrival_net_weight / 1000 if r.arrival_net_weight else None, 3),
            _fmt_float(r.weight_diff / 1000 if r.weight_diff else None, 3),
            ratio_permille,
            r.transport_duration or "",
            _STATUS_LABELS.get(r.status, r.status.value),
            r.alert_count,
            r.notes or "",
        ])

    output.seek(0)
    filename = f"运输记录_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/alerts")
def export_alerts(
    severity: Optional[Severity] = Query(None, description="严重程度筛选"),
    alert_status: Optional[AlertStatus] = Query(None, description="处理状态筛选"),
    alert_type: Optional[AlertType] = Query(None, description="预警类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """导出预警记录为 CSV"""
    query = db.query(Alert).options(
        joinedload(Alert.transport).joinedload(TransportRecord.vehicle)
    )

    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_status:
        query = query.filter(Alert.status == alert_status)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if start_date:
        query = query.filter(Alert.created_at >= start_date)
    if end_date:
        query = query.filter(Alert.created_at <= end_date)

    alerts = query.order_by(Alert.created_at.desc()).all()

    output = io.StringIO()
    output.write("﻿")
    writer = csv.writer(output)
    writer.writerow([
        "预警ID", "车牌号", "出发港口", "运输记录ID",
        "预警类型", "严重程度",
        "描述", "触发阈值", "实际值",
        "处理状态", "处理人", "处理时间", "处理备注",
        "预警时间",
    ])
    for a in alerts:
        plate_no = ""
        dep_port = ""
        if a.transport:
            dep_port = a.transport.departure_port or ""
            if a.transport.vehicle:
                plate_no = a.transport.vehicle.plate_number
        writer.writerow([
            a.id,
            plate_no,
            dep_port,
            a.transport_id,
            _ALERT_TYPE_LABELS.get(a.alert_type, a.alert_type.value),
            _SEVERITY_LABELS.get(a.severity, a.severity.value),
            a.description,
            _fmt_float(a.threshold_value, 6),
            _fmt_float(a.actual_value, 6),
            _ALERT_STATUS_LABELS.get(a.status, a.status.value),
            a.resolved_by or "",
            _fmt_dt(a.resolved_at),
            a.resolution_notes or "",
            _fmt_dt(a.created_at),
        ])

    output.seek(0)
    filename = f"预警记录_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
