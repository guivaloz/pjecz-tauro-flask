"""
API-Key v1 Endpoint: Consultar Configuración Usuario
"""

from flask import request
from flask_restful import Resource
from sqlalchemy import or_
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from tauro.blueprints.api_key_v1.endpoints.autenticar import api_key_required
from tauro.blueprints.api_v1.schemas import (
    RolOut,
    UnidadOut,
    TurnoTipoOut,
    TurnoOut,
    VentanillaOut,
    OneConfiguracionUsuarioOut,
    ConfiguracionUsuarioOut,
)
from tauro.blueprints.api_key_v1.schemas import ConsultarUsuarioIn
from tauro.blueprints.turnos.models import Turno
from tauro.blueprints.turnos_estados.models import TurnoEstado
from tauro.blueprints.usuarios.models import Usuario
from tauro.blueprints.usuarios_turnos_tipos.models import UsuarioTurnoTipo
from tauro.blueprints.ventanillas.models import Ventanilla
from tauro.blueprints.unidades.models import Unidad
from tauro.blueprints.usuarios_roles.models import UsuarioRol


class ConsultarConfiguracionUsuario(Resource):
    """Consultar configuración del usuario"""

    @api_key_required
    def post(self) -> OneConfiguracionUsuarioOut:
        """Consultar configuración del usuario"""

        # Recibir y validar el payload
        payload = request.get_json()
        usuario_in = ConsultarUsuarioIn.model_validate(payload)

        # Consultar el usuario
        try:
            usuario = Usuario.query.filter_by(id=usuario_in.usuario_id).filter_by(estatus="A").one()
        except (MultipleResultsFound, NoResultFound):
            return OneConfiguracionUsuarioOut(
                success=False,
                message="Usuario no encontrado",
            ).model_dump()

        # Consultar los tipos de turnos del usuario
        usuarios_turnos_tipos = (
            UsuarioTurnoTipo.query.filter_by(usuario_id=usuario.id).filter_by(es_activo=True).filter_by(estatus="A").all()
        )
        turnos_tipos = None
        if usuarios_turnos_tipos:
            turnos_tipos = [
                TurnoTipoOut(id=utt.turno_tipo.id, nombre=utt.turno_tipo.nombre, nivel=utt.turno_tipo.nivel)
                for utt in usuarios_turnos_tipos
            ]

        # Consultar el último turno en "EN ESPERA" o "ATENDIENDO" del usuario
        turnos = (
            Turno.query.join(TurnoEstado)
            .filter(or_(TurnoEstado.nombre == "EN ESPERA", TurnoEstado.nombre == "ATENDIENDO"))
            .filter(Turno.usuario_id == usuario.id)
            .filter(Turno.estatus == "A")
            .order_by(Turno.id.desc())
            .first()
        )
        ultimo_turno = None
        if turnos:
            # Consultar la unidad
            unidad = Unidad.query.get(turnos.unidad_id)
            # Extraer la unidad
            unidad_out = None
            if unidad is not None:
                unidad_out = UnidadOut(
                    id=unidad.id,
                    clave=unidad.clave,
                    nombre=unidad.nombre,
                )

            ultimo_turno = TurnoOut(
                turno_id=turnos.id,
                turno_numero=turnos.numero,
                turno_estado=turnos.turno_estado.nombre,
                turno_tipo_id=turnos.turno_tipo_id,
                turno_comentarios=turnos.comentarios,
                ventanilla=VentanillaOut(
                    id=turnos.ventanilla.id,
                    nombre=turnos.ventanilla.nombre,
                    numero=turnos.ventanilla.numero,
                ),
                unidad=unidad_out,
            )
        # Consultar la ventanilla del usuario
        ventanilla_sql = Ventanilla.query.get(usuario.ventanilla_id)
        ventanilla = VentanillaOut(id=ventanilla_sql.id, nombre=ventanilla_sql.nombre, numero=ventanilla_sql.numero)
        # Extraer un único rol
        usuarios_roles = UsuarioRol.query.filter_by(usuario_id=usuario.id).filter_by(estatus="A").first()
        if usuarios_roles is None:
            return OneConfiguracionUsuarioOut(
                success=False,
                message="El usuario no tiene un rol asignado",
            ).model_dump()
        rol = usuarios_roles.rol
        # Consultar la unidad
        unidad_sql = Unidad.query.get(usuario.unidad_id)
        if unidad_sql:
            unidad = UnidadOut(
                id=unidad_sql.id,
                clave=unidad_sql.clave,
                nombre=unidad_sql.nombre,
            )

        # Entregar JSON
        return OneConfiguracionUsuarioOut(
            success=True,
            message=f"Se ha consultado la configuración del usuario {usuario.nombre}",
            data=ConfiguracionUsuarioOut(
                ventanilla=ventanilla,
                unidad=unidad,
                turnos_tipos=turnos_tipos,
                usuario_nombre_completo=usuario.nombre,
                rol=RolOut(
                    id=rol.id,
                    nombre=rol.nombre,
                ),
                ultimo_turno=ultimo_turno,
            ),
        ).model_dump()
