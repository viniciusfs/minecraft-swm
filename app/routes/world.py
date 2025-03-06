from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from app.services.world_service import get_world_details
from app.services.docker_service import update_docker_compose, stop_server, start_server

bp = Blueprint('world', __name__, url_prefix='/world', template_folder='templates')


@bp.route('/<world>')
def world_details(world):
    details = get_world_details(world)
    return render_template('world_details.html', world=details)


@bp.route('/<world>/activate', methods=['POST'])
def activate_world(world):
    if update_docker_compose(world):
        if stop_server() and start_server():
            flash(f'Mundo "{world}" ativado com sucesso!', 'success')
        else:
            flash('Mundo atualizado, mas falha ao reiniciar o servidor!', 'error')
    else:
        flash('Falha ao atualizar o mundo no servidor!', 'error')

    return redirect(url_for('main.index'))
