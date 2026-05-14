"""运输记录API"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.transport import TransportRecord, RecordStatus
from app.models.seal import SealRecord, SealType
from app.models.vehicle import Vehicle
from app.models.alert import Alert
from app.schemas.transport import (
    TransportRecordCreate,
    TransportRecordUpdate,
    TransportRecordResponse,
    TransportListItem,
)
from app.schemas.alert import AlertResponse
from app.services.risk_engine import RiskEngine
from app.utils.helpers import api_response, paginate_response

router = APIRouter(prefix="/api/transports", tags=["运输记录"])

risk_engine = RiskEngine()


@router.get("")
def list_transports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    plate: Optional[str] = Query(None, description="车牌号模糊搜索"),
    status: Optional[RecordStatus] = Query(None, description="记录状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """分页查询运输记录，支持多维度筛选"""
    query = db.query(TransportRecord)

    if plate:
        # 通过车牌号关联筛选
        query = query.join(Vehicle).filter(Vehicle.plate_number.contains(plate))
    if status:
        query = query.filter(TransportRecord.status == status)
    if start_date:
        query = query.filter(TransportRecord.departure_time >= start_date)
    if end_date:
        query = query.filter(TransportRecord.arrival_time <= end_date)

    total = query.count()
    records = (
        query.order_by(TransportRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for r in records:
        item = TransportListItem.model_validate(r).model_dump()
        # 附加车牌号
        vehicle = db.query(Vehicle).filter(Vehicle.id == r.vehicle_id).first()
        item["plate_number"] = vehicle.plate_number if vehicle else "未知"
        items.append(item)

    return api_response(data=paginate_response(items, total, page, page_size))


@router.post("")
def create_transport(
    transport_in: TransportRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    新增运输记录

    创建后自动触发风险检测引擎，生成预警记录。
    """
    # 校验车辆存在
    vehicle = db.query(Vehicle).filter(Vehicle.id == transport_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")

    # 计算衍生字段
    weight_diff = transport_in.arrival_net_weight - transport_in.departure_net_weight
    weight_diff_ratio = weight_diff / transport_in.departure_net_weight if transport_in.departure_net_weight else 0
    duration = int((transport_in.arrival_time - transport_in.departure_time).total_seconds() / 60)

    # 创建运输记录
    transport = TransportRecord(
        vehicle_id=transport_in.vehicle_id,
        departure_port=transport_in.departure_port,
        departure_weight=transport_in.departure_weight,
        departure_net_weight=transport_in.departure_net_weight,
        departure_time=transport_in.departure_time,
        arrival_weight=transport_in.arrival_weight,
        arrival_net_weight=transport_in.arrival_net_weight,
        arrival_time=transport_in.arrival_time,
        weight_diff=round(weight_diff, 2),
        weight_diff_ratio=round(weight_diff_ratio, 6),
        transport_duration=duration,
        notes=transport_in.notes,
    )
    db.add(transport)
    db.flush()  # 获取ID

    # 创建铅封记录
    if transport_in.departure_seal_qr is not None:
        dep_seal = SealRecord(
            qr_code=transport_in.departure_seal_qr,
            seal_type=SealType.DEPARTURE,
            is_valid=transport_in.departure_seal_valid,
            scan_time=transport_in.departure_time,
            transport_id=transport.id,
        )
        db.add(dep_seal)
        db.flush()
        transport.departure_seal_id = dep_seal.id

    if transport_in.arrival_seal_qr is not None:
        arr_seal = SealRecord(
            qr_code=transport_in.arrival_seal_qr,
            seal_type=SealType.ARRIVAL,
            is_valid=transport_in.arrival_seal_valid,
            scan_time=transport_in.arrival_time,
            transport_id=transport.id,
        )
        db.add(arr_seal)
        db.flush()
        transport.arrival_seal_id = arr_seal.id

    db.flush()

    # 触发风险检测引擎
    alerts = risk_engine.evaluate(transport, db)
    risk_score = risk_engine.compute_risk_score(alerts)

    db.refresh(transport)

    result = TransportRecordResponse.model_validate(transport).model_dump()
    result["risk_score"] = risk_score
    result["alerts_count"] = len(alerts)

    return api_response(message="运输记录创建成功，已完成风险检测", data=result)


@router.get("/{transport_id}")
def get_transport(
    transport_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取运输记录详情"""
    record = db.query(TransportRecord).filter(TransportRecord.id == transport_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="运输记录不存在")

    result = TransportRecordResponse.model_validate(record).model_dump()

    # 附加车牌号
    vehicle = db.query(Vehicle).filter(Vehicle.id == record.vehicle_id).first()
    result["plate_number"] = vehicle.plate_number if vehicle else "未知"

    # 附加预警列表
    alerts = db.query(Alert).filter(Alert.transport_id == transport_id).all()
    result["alerts"] = [AlertResponse.model_validate(a).model_dump() for a in alerts]

    return api_response(data=result)


@router.get("/{transport_id}/alerts")
def get_transport_alerts(
    transport_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取指定运输记录的所有预警"""
    record = db.query(TransportRecord).filter(TransportRecord.id == transport_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="运输记录不存在")

    alerts = db.query(Alert).filter(Alert.transport_id == transport_id).all()
    items = [AlertResponse.model_validate(a).model_dump() for a in alerts]

    return api_response(data=items)


@router.put("/{transport_id}")
def update_transport(
    transport_id: int,
    transport_in: TransportRecordUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新运输记录（仅允许更新部分字段）"""
    record = db.query(TransportRecord).filter(TransportRecord.id == transport_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="运输记录不存在")

    update_data = transport_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)

    # 如果更新了进厂数据，重新计算衍生字段
    if record.departure_net_weight and record.arrival_net_weight:
        record.weight_diff = round(record.arrival_net_weight - record.departure_net_weight, 2)
        record.weight_diff_ratio = round(record.weight_diff / record.departure_net_weight, 6)
    if record.departure_time and record.arrival_time:
        record.transport_duration = int((record.arrival_time - record.departure_time).total_seconds() / 60)

    db.commit()
    db.refresh(record)
    return api_response(message="运输记录更新成功", data=TransportRecordResponse.model_validate(record).model_dump())
