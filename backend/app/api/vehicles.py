"""车辆管理API"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.transport import TransportRecord
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListItem
from app.schemas.transport import TransportRecordResponse
from app.utils.helpers import api_response, paginate_response

router = APIRouter(prefix="/api/vehicles", tags=["车辆管理"])


@router.get("")
def list_vehicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    plate: Optional[str] = Query(None, description="车牌号模糊搜索"),
    status: Optional[VehicleStatus] = Query(None, description="车辆状态筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """分页查询车辆列表"""
    query = db.query(Vehicle)
    if plate:
        query = query.filter(Vehicle.plate_number.contains(plate))
    if status:
        query = query.filter(Vehicle.status == status)

    total = query.count()
    vehicles = query.order_by(Vehicle.id).offset((page - 1) * page_size).limit(page_size).all()

    items = [VehicleListItem.model_validate(v).model_dump() for v in vehicles]
    return api_response(data=paginate_response(items, total, page, page_size))


@router.post("")
def create_vehicle(
    vehicle_in: VehicleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """新增车辆"""
    existing = db.query(Vehicle).filter(Vehicle.plate_number == vehicle_in.plate_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="车牌号已存在")

    vehicle = Vehicle(**vehicle_in.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return api_response(message="车辆创建成功", data=VehicleResponse.model_validate(vehicle).model_dump())


@router.get("/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取车辆详情"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")
    return api_response(data=VehicleResponse.model_validate(vehicle).model_dump())


@router.put("/{vehicle_id}")
def update_vehicle(
    vehicle_id: int,
    vehicle_in: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新车辆信息"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")

    update_data = vehicle_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)
    return api_response(message="车辆更新成功", data=VehicleResponse.model_validate(vehicle).model_dump())


@router.get("/{plate}/history")
def get_vehicle_history(
    plate: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取指定车辆的运输历史"""
    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="车辆不存在")

    query = db.query(TransportRecord).filter(TransportRecord.vehicle_id == vehicle.id)
    total = query.count()
    records = (
        query.order_by(TransportRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [TransportRecordResponse.model_validate(r).model_dump() for r in records]
    return api_response(data=paginate_response(items, total, page, page_size))
