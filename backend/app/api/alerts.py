"""预警管理API"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.alert import Alert, AlertType, Severity, AlertStatus
from app.models.transport import TransportRecord
from app.models.vehicle import Vehicle
from app.schemas.alert import AlertResponse, AlertAcknowledgeRequest, AlertResolveRequest, AlertStats
from app.utils.helpers import api_response, paginate_response

router = APIRouter(prefix="/api/alerts", tags=["预警管理"])


@router.get("")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    alert_type: Optional[AlertType] = Query(None, description="预警类型"),
    severity: Optional[Severity] = Query(None, description="严重程度"),
    status: Optional[AlertStatus] = Query(None, description="处理状态"),
    plate: Optional[str] = Query(None, description="车牌号"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """分页查询预警列表，支持多维度筛选"""
    query = db.query(Alert)

    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if severity:
        query = query.filter(Alert.severity == severity)
    if status:
        query = query.filter(Alert.status == status)
    if plate:
        query = (
            query.join(TransportRecord)
            .join(Vehicle)
            .filter(Vehicle.plate_number.contains(plate))
        )

    total = query.count()
    alerts = (
        query.order_by(Alert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for a in alerts:
        item = AlertResponse.model_validate(a).model_dump()
        # 附加车牌号和运输信息
        transport = db.query(TransportRecord).filter(TransportRecord.id == a.transport_id).first()
        if transport:
            vehicle = db.query(Vehicle).filter(Vehicle.id == transport.vehicle_id).first()
            item["plate_number"] = vehicle.plate_number if vehicle else "未知"
            item["departure_port"] = transport.departure_port
            item["departure_time"] = transport.departure_time.isoformat() if transport.departure_time else None
        items.append(item)

    return api_response(data=paginate_response(items, total, page, page_size))


@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    body: Optional[AlertAcknowledgeRequest] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """确认预警（标记为已确认）"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")

    if alert.status != AlertStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"当前状态为{alert.status.value}，无法确认")

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.resolved_by = current_user.username
    alert.resolved_at = datetime.utcnow()
    db.commit()

    return api_response(message="预警已确认", data=AlertResponse.model_validate(alert).model_dump())


@router.put("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    body: AlertResolveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """处理预警（标记为已解决，需填写处理备注）"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")

    if alert.status in (AlertStatus.RESOLVED, AlertStatus.DISMISSED):
        raise HTTPException(status_code=400, detail="该预警已处理")

    alert.status = AlertStatus.RESOLVED
    alert.resolved_by = current_user.username
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = body.resolution_notes
    db.commit()

    return api_response(message="预警已处理", data=AlertResponse.model_validate(alert).model_dump())


@router.put("/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """忽略预警（标记为已忽略）"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")

    alert.status = AlertStatus.DISMISSED
    alert.resolved_by = current_user.username
    alert.resolved_at = datetime.utcnow()
    db.commit()

    return api_response(message="预警已忽略", data=AlertResponse.model_validate(alert).model_dump())


@router.get("/stats")
def get_alert_stats(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取预警统计数据"""
    cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0) - __import__('datetime').timedelta(days=days)

    # 按类型统计
    type_stats = (
        db.query(Alert.alert_type, func.count(Alert.id))
        .filter(Alert.created_at >= cutoff)
        .group_by(Alert.alert_type)
        .all()
    )

    # 按严重程度统计
    severity_stats = (
        db.query(Alert.severity, func.count(Alert.id))
        .filter(Alert.created_at >= cutoff)
        .group_by(Alert.severity)
        .all()
    )

    # 按状态统计
    status_stats = (
        db.query(Alert.status, func.count(Alert.id))
        .filter(Alert.created_at >= cutoff)
        .group_by(Alert.status)
        .all()
    )

    return api_response(data={
        "by_type": {t.value: c for t, c in type_stats},
        "by_severity": {s.value: c for s, c in severity_stats},
        "by_status": {s.value: c for s, c in status_stats},
        "total": sum(c for _, c in type_stats),
        "days": days,
    })
