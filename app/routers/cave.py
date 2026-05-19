# app/routers/cave.py

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cave, Wall, Zone, User
from app.routers.auth import require_user
from app.services.simulation import simulate_cave
from app.services.materials import get_material_properties
from app.services.renovation import (
    generate_renovation_scenarios,
    calculate_scenario,
)
from app.services.pdf import generate_cave_report_pdf

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def render_template(
    request: Request,
    template_name: str,
    context: dict | None = None,
):
    if context is None:
        context = {}

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context,
    )


def get_user_cave(
    db: Session,
    cave_id: int,
    current_user: User,
) -> Cave:
    cave = db.query(Cave).filter(
        Cave.id == cave_id,
        Cave.user_id == current_user.id,
    ).first()

    if not cave:
        raise HTTPException(status_code=404, detail="Cave introuvable.")

    return cave


@router.get("/")
def home():
    return RedirectResponse(url="/login", status_code=303)


@router.get("/caves")
def caves_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    caves = db.query(Cave).filter(
        Cave.user_id == current_user.id,
    ).all()

    return render_template(
        request,
        "caves_list.html",
        {"caves": caves},
    )


@router.get("/caves/new")
def cave_form(
    request: Request,
    current_user: User = Depends(require_user),
):
    return render_template(
        request,
        "cave_form.html",
    )


@router.post("/caves")
def create_cave(
    name: str = Form(...),
    region: str = Form(...),
    altitude_m: float = Form(...),
    length_m: float = Form(...),
    width_m: float = Form(...),
    height_m: float = Form(...),
    buried_factor: float = Form(...),
    wall_n_material: str = Form(...),
    wall_n_u: float = Form(...),
    wall_s_material: str = Form(...),
    wall_s_u: float = Form(...),
    wall_e_material: str = Form(...),
    wall_e_u: float = Form(...),
    wall_w_material: str = Form(...),
    wall_w_u: float = Form(...),
    roof_material: str = Form(...),
    roof_u: float = Form(...),
    floor_material: str = Form(...),
    floor_u: float = Form(...),
    zone_count: int = Form(...),
    energy_source: str = Form(...),
    energy_price_chf_per_kwh: float = Form(...),
    co2_factor_kg_per_kwh: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if zone_count < 1:
        raise HTTPException(
            status_code=400,
            detail="Le nombre de zones doit être au moins 1.",
        )

    cave = Cave(
        name=name,
        user_id=current_user.id,
        region=region,
        altitude_m=altitude_m,
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        buried_factor=buried_factor,
        energy_source=energy_source,
        energy_price_chf_per_kwh=energy_price_chf_per_kwh,
        co2_factor_kg_per_kwh=co2_factor_kg_per_kwh,
    )

    db.add(cave)
    db.flush()

    wall_height_area_long = length_m * height_m
    wall_height_area_short = width_m * height_m
    roof_floor_area = length_m * width_m

    wall_inputs = [
        ("Mur Nord", "N", wall_n_material, wall_height_area_long, wall_n_u),
        ("Mur Sud", "S", wall_s_material, wall_height_area_long, wall_s_u),
        ("Mur Est", "E", wall_e_material, wall_height_area_short, wall_e_u),
        ("Mur Ouest", "O", wall_w_material, wall_height_area_short, wall_w_u),
        ("Toiture", "H", roof_material, roof_floor_area, roof_u),
        ("Sol", "B", floor_material, roof_floor_area, floor_u),
    ]

    walls = []

    for wall_name, orientation, material, area, u_value in wall_inputs:
        props = get_material_properties(material)

        walls.append(
            Wall(
                cave_id=cave.id,
                name=wall_name,
                orientation=orientation,
                material=material,
                area_m2=area,
                u_value=u_value,
                thickness_m=props["default_thickness_m"],
                inertia_factor=props["inertia_factor"],
            )
        )

    db.add_all(walls)

    total_volume = length_m * width_m * height_m
    default_zone_volume = total_volume / zone_count

    for i in range(zone_count):
        zone_length = length_m / zone_count

        zone = Zone(
            cave_id=cave.id,
            name=f"Zone {i + 1}",
            volume_m3=default_zone_volume,
            target_temp_winter_c=12,
            target_temp_summer_c=16,
            target_humidity_percent=75,
            process_cooling_kwh=0,
            process_heating_kwh=0,
            x_m=i * zone_length,
            y_m=0,
            width_m=width_m,
            length_m=zone_length,
        )
        db.add(zone)

    db.commit()

    return RedirectResponse(
        url=f"/caves/{cave.id}",
        status_code=303,
    )


@router.get("/caves/{cave_id}")
def cave_detail(
    cave_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)

    return render_template(
        request,
        "cave_detail.html",
        {"cave": cave},
    )


@router.post("/zones/{zone_id}/update")
def update_zone(
    zone_id: int,
    name: str = Form(...),
    volume_m3: float = Form(...),
    x_m: float = Form(0),
    y_m: float = Form(0),
    width_m: float = Form(1),
    length_m: float = Form(1),
    target_temp_winter_c: float = Form(...),
    target_temp_summer_c: float = Form(...),
    target_humidity_percent: float = Form(...),
    process_cooling_kwh: float = Form(0),
    process_heating_kwh: float = Form(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    zone = db.query(Zone).join(Cave).filter(
        Zone.id == zone_id,
        Cave.user_id == current_user.id,
    ).first()

    if not zone:
        raise HTTPException(status_code=404, detail="Zone introuvable.")

    zone.name = name
    zone.volume_m3 = volume_m3
    zone.x_m = x_m
    zone.y_m = y_m
    zone.width_m = width_m
    zone.length_m = length_m
    zone.target_temp_winter_c = target_temp_winter_c
    zone.target_temp_summer_c = target_temp_summer_c
    zone.target_humidity_percent = target_humidity_percent
    zone.process_cooling_kwh = process_cooling_kwh
    zone.process_heating_kwh = process_heating_kwh

    cave_id = zone.cave_id
    db.commit()

    return RedirectResponse(
        url=f"/caves/{cave_id}",
        status_code=303,
    )


@router.get("/caves/{cave_id}/simulate")
def simulate(
    cave_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)
    result = simulate_cave(cave)

    return render_template(
        request,
        "simulation_result.html",
        {
            "cave": cave,
            "result": result,
        },
    )


@router.get("/caves/{cave_id}/renovation")
def renovation(
    cave_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)
    scenarios = generate_renovation_scenarios(cave)

    return render_template(
        request,
        "renovation_result.html",
        {
            "cave": cave,
            "scenarios": scenarios,
        },
    )


@router.get("/caves/{cave_id}/renovation/custom")
def renovation_custom_form(
    cave_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)

    return render_template(
        request,
        "renovation_custom_form.html",
        {"cave": cave},
    )


@router.post("/caves/{cave_id}/renovation/custom")
def renovation_custom_result(
    cave_id: int,
    request: Request,
    scenario_name: str = Form(...),
    investment_chf: float = Form(...),
    roof_reduction_percent: float = Form(...),
    walls_reduction_percent: float = Form(...),
    floor_reduction_percent: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)

    def wall_filter(wall):
        if wall.name == "Toiture" and roof_reduction_percent > 0:
            return True

        if wall.orientation in ["N", "S", "E", "O"] and walls_reduction_percent > 0:
            return True

        if wall.name == "Sol" and floor_reduction_percent > 0:
            return True

        return False

    reductions = []

    if roof_reduction_percent > 0:
        reductions.append(roof_reduction_percent)

    if walls_reduction_percent > 0:
        reductions.append(walls_reduction_percent)

    if floor_reduction_percent > 0:
        reductions.append(floor_reduction_percent)

    average_reduction_percent = sum(reductions) / len(reductions) if reductions else 0
    reduction_factor = 1 - (average_reduction_percent / 100)

    scenario = calculate_scenario(
        cave=cave,
        name=scenario_name,
        description=(
            f"Toiture: -{roof_reduction_percent} %, "
            f"murs: -{walls_reduction_percent} %, "
            f"sol: -{floor_reduction_percent} % sur les valeurs U."
        ),
        investment_chf=investment_chf,
        wall_filter=wall_filter,
        reduction_factor=reduction_factor,
    )

    return render_template(
        request,
        "renovation_custom_result.html",
        {
            "cave": cave,
            "scenario": scenario,
            "roof_reduction_percent": roof_reduction_percent,
            "walls_reduction_percent": walls_reduction_percent,
            "floor_reduction_percent": floor_reduction_percent,
        },
    )


@router.get("/caves/{cave_id}/report/pdf")
def cave_report_pdf(
    cave_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)
    pdf_bytes = generate_cave_report_pdf(request, cave)

    filename = f"rapport_simulcave_{cave.id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )

@router.get("/caves/{cave_id}/plan")
def cave_plan(
    cave_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)

    return render_template(
        request,
        "cave_plan.html",
        {"cave": cave},
    )

@router.get("/caves/{cave_id}/parameters")
def cave_parameters(
    cave_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)

    result = simulate_cave(cave)

    return render_template(
        request,
        "cave_parameters.html",
        {
            "cave": cave,
            "result": result,
        },
    )

@router.post("/walls/{wall_id}/update")
def update_wall(
    wall_id: int,
    material: str = Form(...),
    area_m2: float = Form(...),
    u_value: float = Form(...),
    thickness_m: float = Form(...),
    inertia_factor: float = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    wall = db.query(Wall).join(Cave).filter(
        Wall.id == wall_id,
        Cave.user_id == current_user.id,
    ).first()

    if not wall:
        raise HTTPException(status_code=404, detail="Paroi introuvable.")

    wall.material = material
    wall.area_m2 = area_m2
    wall.u_value = u_value
    wall.thickness_m = thickness_m
    wall.inertia_factor = inertia_factor

    cave_id = wall.cave_id

    db.commit()

    return RedirectResponse(
        url=f"/caves/{cave_id}",
        status_code=303,
    )

@router.post("/caves/{cave_id}/delete")
def delete_cave(
    cave_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    cave = get_user_cave(db, cave_id, current_user)

    db.delete(cave)
    db.commit()

    return RedirectResponse(url="/caves", status_code=303)