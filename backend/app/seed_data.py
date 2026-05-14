"""种子数据生成器：创建演示用的车辆、运输记录和预警数据"""
import sys
import os
import random
from datetime import datetime, timedelta

# 将backend目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import *
from app.services.risk_engine import RiskEngine
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 车牌号列表（模拟真实车辆）
PLATES = [
    "粤A12345", "粤A23456", "粤A34567", "粤A45678", "粤A56789",
    "粤B11111", "粤B22222", "粤B33333", "粤B44444", "粤B55555",
    "桂C10086", "桂C20086", "桂C30086", "湘D88888", "湘D99999",
]

# 司机信息
DRIVERS = [
    ("张三", "13800001111"), ("李四", "13800002222"), ("王五", "13800003333"),
    ("赵六", "13800004444"), ("孙七", "13800005555"), ("周八", "13800006666"),
    ("吴九", "13800007777"), ("郑十", "13800008888"), ("陈一", "13800009999"),
    ("林二", "13800000000"), ("黄三", "13810001111"), ("刘四", "13820002222"),
    ("杨五", "13830003333"), ("何六", "13840004444"), ("马七", "13850005555"),
]

# 港口名称
PORTS = ["南江口码头", "沙角A码头", "珠海高栏港"]

# 铅封二维码前缀
SEAL_PREFIX = "SEAL-2024"


def generate_qr_code(seq: int) -> str:
    """生成模拟铅封二维码"""
    return f"{SEAL_PREFIX}-{seq:06d}"


def seed_data():
    """生成种子数据"""
    # 创建表
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    risk_engine = RiskEngine()

    try:
        # 检查是否已有数据
        existing = db.query(Vehicle).count()
        if existing > 0:
            print(f"[跳过] 数据库已有{existing}条车辆记录，跳过种子数据生成")
            return

        print("[开始] 生成种子数据...")

        # 1. 创建管理员用户
        admin = User(
            username="admin",
            hashed_password=pwd_context.hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        operator = User(
            username="operator",
            hashed_password=pwd_context.hash("operator123"),
            role=UserRole.OPERATOR,
            is_active=True,
        )
        viewer = User(
            username="viewer",
            hashed_password=pwd_context.hash("viewer123"),
            role=UserRole.VIEWER,
            is_active=True,
        )
        db.add_all([admin, operator, viewer])
        print("[完成] 创建3个用户账户")

        # 2. 创建车辆
        vehicles = []
        for i, plate in enumerate(PLATES):
            driver_name, driver_phone = DRIVERS[i % len(DRIVERS)]
            v = Vehicle(
                plate_number=plate,
                tare_weight=random.uniform(12000, 16000),  # 皮重12-16吨
                driver_name=driver_name,
                driver_phone=driver_phone,
                status=VehicleStatus.ACTIVE,
            )
            db.add(v)
            vehicles.append(v)
        db.flush()
        print(f"[完成] 创建{len(vehicles)}辆车辆")

        # 3. 创建运输记录（50+条，包含正常和异常）
        seal_seq = 1
        base_time = datetime.utcnow() - timedelta(days=30)

        for idx in range(60):
            vehicle = random.choice(vehicles)
            port = random.choice(PORTS)

            # 出发时间（按序递增，模拟真实节奏）
            departure_time = base_time + timedelta(hours=idx * 8 + random.uniform(0, 2))

            # 正常运输时长：3-5小时
            normal_duration = random.uniform(180, 300)

            # 10%概率制造时间异常
            if random.random() < 0.10:
                # 超时30-90分钟
                actual_duration = normal_duration + random.uniform(35, 90)
            else:
                actual_duration = normal_duration + random.uniform(-10, 15)

            arrival_time = departure_time + timedelta(minutes=actual_duration)

            # 出港净重：28-35吨（正常煤炭装载量）
            departure_net = random.uniform(28000, 35000)
            departure_gross = departure_net + vehicle.tare_weight

            # 正常重量偏差：±1‰以内
            # 8%概率制造重量异常
            if random.random() < 0.04:
                # 亏吨：偏差5-15‰
                weight_ratio = -random.uniform(0.005, 0.015)
                arrival_net = departure_net * (1 + weight_ratio)
            elif random.random() < 0.04:
                # 盈吨：偏差4-10‰
                weight_ratio = random.uniform(0.004, 0.010)
                arrival_net = departure_net * (1 + weight_ratio)
            else:
                # 正常偏差
                weight_ratio = random.uniform(-0.002, 0.002)
                arrival_net = departure_net * (1 + weight_ratio)

            arrival_gross = arrival_net + vehicle.tare_weight
            weight_diff = arrival_net - departure_net

            # 铅封二维码
            dep_qr = generate_qr_code(seal_seq)
            # 5%概率铅封异常
            if random.random() < 0.05:
                arr_qr = generate_qr_code(seal_seq + 1000)  # 不一致
            else:
                arr_qr = dep_qr  # 正常一致

            seal_valid = random.random() > 0.03  # 3%概率铅封损坏

            # 创建铅封记录
            dep_seal = SealRecord(
                qr_code=dep_qr,
                seal_type=SealType.DEPARTURE,
                is_valid=True,
                scan_time=departure_time,
            )
            db.add(dep_seal)
            db.flush()

            arr_seal = SealRecord(
                qr_code=arr_qr,
                seal_type=SealType.ARRIVAL,
                is_valid=seal_valid,
                scan_time=arrival_time,
            )
            db.add(arr_seal)
            db.flush()

            # 创建运输记录
            transport = TransportRecord(
                vehicle_id=vehicle.id,
                departure_port=port,
                departure_weight=round(departure_gross, 2),
                departure_net_weight=round(departure_net, 2),
                departure_time=departure_time,
                departure_seal_id=dep_seal.id,
                arrival_weight=round(arrival_gross, 2),
                arrival_net_weight=round(arrival_net, 2),
                arrival_time=arrival_time,
                arrival_seal_id=arr_seal.id,
                weight_diff=round(weight_diff, 2),
                weight_diff_ratio=round(weight_diff / departure_net, 6),
                transport_duration=int(actual_duration),
            )
            db.add(transport)
            db.flush()

            # 更新铅封记录的运输ID
            dep_seal.transport_id = transport.id
            arr_seal.transport_id = transport.id

            # 触发风险检测（前20条不检测，模拟系统上线前的数据）
            if idx >= 20:
                alerts = risk_engine.evaluate(transport, db)
                if alerts:
                    print(f"  [预警] 记录#{idx + 1} {vehicle.plate_number}: {len(alerts)}条预警")

            seal_seq += 1

        db.commit()
        total_transports = db.query(TransportRecord).count()
        total_alerts = db.query(Alert).count()
        print(f"\n[完成] 种子数据生成完毕:")
        print(f"  - 车辆: {len(vehicles)}辆")
        print(f"  - 运输记录: {total_transports}条")
        print(f"  - 预警记录: {total_alerts}条")
        print(f"  - 用户: admin/admin123, operator/operator123, viewer/viewer123")

    except Exception as e:
        db.rollback()
        print(f"[错误] 种子数据生成失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
