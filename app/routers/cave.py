# app/routers/cave.py

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cave, Wall, Zone
from app.services.simulation import simulate_cave

router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


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


@router.get("/")
def home():
    return RedirectResponse(url="/caves", status_code=303)


@router.get("/caves")
def caves_list(request: Request, db: Session = Depends(get_db)):
    caves = db.query(Cave).all()

    return render_template(
        request,
        "caves_list.html",
        {"caves": caves},
    )


@router.get("/caves/new")
def cave_form(request: Request):
    return render_template(
        request,
        "cave_form.html",
    )


@router.post("/caves")
def create_cave(
    name: str = Form(...),
    region: str = Form(...),
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
    db: Session = Depends(get_db),
):
    if zone_count < 1:
        raise HTTPException(
            status_code=400,
            detail="Le nombre de zones doit être au moins 1.",
        )

    cave = Cave(
        name=name,
        region=region,
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        buried_factor=buried_factor,
    )

    db.add(cave)
    db.flush()

    wall_height_area_long = length_m * height_m
    wall_height_area_short = width_m * height_m
    roof_floor_area = length_m * width_m

    walls = [
        Wall(
            cave_id=cave.id,
            name="Mur Nord",
            orientation="N",
            material=wall_n_material,
            area_m2=wall_height_area_long,
            u_value=wall_n_u,
        ),
        Wall(
            cave_id=cave.id,
            name="Mur Sud",
            orientation="S",
            material=wall_s_material,
            area_m2=wall_height_area_long,
            u_value=wall_s_u,
        ),
        Wall(
            cave_id=cave.id,
            name="Mur Est",
            orientation="E",
            material=wall_e_material,
            area_m2=wall_height_area_short,
            u_value=wall_e_u,
        ),
        Wall(
            cave_id=cave.id,
            name="Mur Ouest",
            orientation="O",
            material=wall_w_material,
            area_m2=wall_height_area_short,
            u_value=wall_w_u,
        ),
        Wall(
            cave_id=cave.id,
            name="Toiture",
            orientation="H",
            material=roof_material,
            area_m2=roof_floor_area,
            u_value=roof_u,
        ),
        Wall(
            cave_id=cave.id,
            name="Sol",
            orientation="B",
            material=floor_material,
            area_m2=roof_floor_area,
            u_value=floor_u,
        ),
    ]

    db.add_all(walls)

    total_volume = length_m * width_m * height_m
    default_zone_volume = total_volume / zone_count

    for i in range(zone_count):
        zone = Zone(
            cave_id=cave.id,
            name=f"Zone {i + 1}",
            volume_m3=default_zone_volume,
            target_temp_winter_c=12,
            target_temp_summer_c=16,
            target_humidity_percent=75,
            process_cooling_kwh=0,
            process_heating_kwh=0,
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
):
    cave = db.query(Cave).filter(Cave.id == cave_id).first()

    if not cave:
        raise HTTPException(status_code=404, detail="Cave introuvable.")

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
    target_temp_winter_c: float = Form(...),
    target_temp_summer_c: float = Form(...),
    target_humidity_percent: float = Form(...),
    process_cooling_kwh: float = Form(...),
    process_heating_kwh: float = Form(...),
    db: Session = Depends(get_db),
):
    zone = db.query(Zone).filter(Zone.id == zone_id).first()

    if not zone:
        raise HTTPException(status_code=404, detail="Zone introuvable.")

    zone.name = name
    zone.volume_m3 = volume_m3
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
):
    cave = db.query(Cave).filter(Cave.id == cave_id).first()

    if not cave:
        raise HTTPException(status_code=404, detail="Cave introuvable.")

    result = simulate_cave(cave)

    return render_template(
        request,
        "simulation_result.html",
        {
            "cave": cave,
            "result": result,
        },
    )


@router.post("/caves/{cave_id}/delete")
def delete_cave(
    cave_id: int,
    db: Session = Depends(get_db),
):
    cave = db.query(Cave).filter(Cave.id == cave_id).first()

    if cave:
        db.delete(cave)
        db.commit()

    return RedirectResponse(url="/caves", status_code=303)