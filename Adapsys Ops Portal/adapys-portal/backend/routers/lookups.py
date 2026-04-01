import json
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.backup_sync import persist_backup_snapshot
from backend.routers.security import RequestActor, get_request_actor, require_roles

router = APIRouter()


class Consultant(BaseModel):
    name: str
    email: str


class ClientProgram(BaseModel):
    client_name: str
    program_name: str


class ConsultantListUpdate(BaseModel):
    items: list[Consultant]


class ClientProgramListUpdate(BaseModel):
    items: list[ClientProgram]


class LookupAdminConfigUpdate(BaseModel):
    consultants: list[Consultant]
    coaches: list[Consultant]
    client_programs: list[ClientProgram]


_DEFAULT_CONSULTANTS: list[Consultant] = [
    Consultant(name="Megan Streeter", email="megan.streeter@adapsysgroup.com"),
    Consultant(name="Cameron Bowles", email="cameron.bowles@adapsysgroup.com"),
    Consultant(name="Diana Renner", email="diana.renner@adapsysgroup.com"),
    Consultant(name="Kate Tucker", email="kate.tucker@adapsysgroup.com"),
    Consultant(name="Diego Rodriguez", email="diego.rodriguez@adapsysgroup.com"),
    Consultant(name="Collette Brown", email="collette.brown@adapsysgroup.com"),
]


_DEFAULT_COACHES: list[Consultant] = [
    *_DEFAULT_CONSULTANTS,
    Consultant(name="Tony Liston", email="tony.liston@adapsysgroup.com"),
]

_DEFAULT_CLIENT_PROGRAMS: list[ClientProgram] = [
    ClientProgram(client_name="MHC", program_name=""),
    ClientProgram(client_name="PFLP", program_name=""),
    ClientProgram(client_name="SPC", program_name=""),
    ClientProgram(client_name="ARTC", program_name=""),
    ClientProgram(client_name="ATI", program_name=""),
    ClientProgram(client_name="NSW Dept of HDA", program_name=""),
    ClientProgram(client_name="Mindaroo", program_name=""),
    ClientProgram(client_name="SILA", program_name=""),
]


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_CONSULTANTS_FILE = _DATA_DIR / "lookups_consultants.json"
_COACHES_FILE = _DATA_DIR / "lookups_coaches.json"
_CLIENT_PROGRAMS_FILE = _DATA_DIR / "lookups_client_programs.json"


def _load_lookup_items(file_path: Path, model_cls, fallback_items: list):
    if not file_path.exists():
        return list(fallback_items)
    try:
        rows = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            return list(fallback_items)
        return [model_cls(**row) for row in rows]
    except Exception:
        return list(fallback_items)


def _save_lookup_items(file_path: Path, items: list[BaseModel]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [item.model_dump(mode="json") for item in items]
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    persist_backup_snapshot(file_path.stem, payload)


_CONSULTANTS: list[Consultant] = _load_lookup_items(
    _CONSULTANTS_FILE,
    Consultant,
    _DEFAULT_CONSULTANTS,
)
_COACHES: list[Consultant] = _load_lookup_items(
    _COACHES_FILE,
    Consultant,
    _DEFAULT_COACHES,
)
_CLIENT_PROGRAMS: list[ClientProgram] = _load_lookup_items(
    _CLIENT_PROGRAMS_FILE,
    ClientProgram,
    _DEFAULT_CLIENT_PROGRAMS,
)


@router.get("/consultants")
def list_consultants() -> list[Consultant]:
    return _CONSULTANTS


@router.get("/coaches")
def list_coaches() -> list[Consultant]:
    return _COACHES


@router.get("/client-programs")
def list_client_programs() -> list[ClientProgram]:
    return _CLIENT_PROGRAMS


@router.get("/admin-config")
def get_lookup_admin_config(actor: RequestActor = Depends(get_request_actor)) -> dict:
    require_roles(actor, {"admin", "finance"})
    return {
        "consultants": _CONSULTANTS,
        "coaches": _COACHES,
        "client_programs": _CLIENT_PROGRAMS,
    }


@router.put("/consultants")
def update_consultants(
    payload: ConsultantListUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> list[Consultant]:
    require_roles(actor, {"admin", "finance"})
    global _CONSULTANTS
    _CONSULTANTS = payload.items
    _save_lookup_items(_CONSULTANTS_FILE, _CONSULTANTS)
    return _CONSULTANTS


@router.put("/coaches")
def update_coaches(
    payload: ConsultantListUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> list[Consultant]:
    require_roles(actor, {"admin", "finance"})
    global _COACHES
    _COACHES = payload.items
    _save_lookup_items(_COACHES_FILE, _COACHES)
    return _COACHES


@router.put("/client-programs")
def update_client_programs(
    payload: ClientProgramListUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> list[ClientProgram]:
    require_roles(actor, {"admin", "finance"})
    global _CLIENT_PROGRAMS
    _CLIENT_PROGRAMS = payload.items
    _save_lookup_items(_CLIENT_PROGRAMS_FILE, _CLIENT_PROGRAMS)
    return _CLIENT_PROGRAMS


@router.put("/admin-config")
def update_lookup_admin_config(
    payload: LookupAdminConfigUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> dict:
    require_roles(actor, {"admin", "finance"})
    global _CONSULTANTS, _COACHES, _CLIENT_PROGRAMS
    _CONSULTANTS = payload.consultants
    _COACHES = payload.coaches
    _CLIENT_PROGRAMS = payload.client_programs
    _save_lookup_items(_CONSULTANTS_FILE, _CONSULTANTS)
    _save_lookup_items(_COACHES_FILE, _COACHES)
    _save_lookup_items(_CLIENT_PROGRAMS_FILE, _CLIENT_PROGRAMS)
    return {
        "consultants": _CONSULTANTS,
        "coaches": _COACHES,
        "client_programs": _CLIENT_PROGRAMS,
    }
