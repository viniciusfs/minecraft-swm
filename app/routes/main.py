from flask import Blueprint, render_template, flash, redirect, url_for, current_app, request

from app.services.compose import get_server_status, start_server, stop_server, update_docker_compose
from app.services.world import get_world_list, get_world_details

bp = Blueprint('main', __name__, template_folder='templates')


@bp.route('/')
def index():
    server_status = get_server_status()

    worlds = []
    for world in get_world_list():
        worlds.append(get_world_details(world))

    return render_template('index.html', worlds=worlds, server_status=server_status)


@bp.route('/world/<world>')
def world_details(world):
    details = get_world_details(world)
    return render_template('world_details.html', world=details)


@bp.route('/world/<world>/activate', methods=['POST'])
def activate_world(world):
    if update_docker_compose(world):
        if stop_server() and start_server():
            flash(f'Mundo "{world}" ativado com sucesso!', 'success')
        else:
            flash('Mundo atualizado, mas falha ao reiniciar o servidor!', 'error')
    else:
        flash('Falha ao atualizar o mundo no servidor!', 'error')

    return redirect(url_for('main.index'))


@bp.route('/restart', methods=['POST'])
def restart_server():
    if stop_server():
        if start_server():
            flash('Servidor reiniciado com sucesso!', 'success')
        else:
            flash('Falha ao iniciar o servidor!', 'error')
    else:
        flash('Falha ao parar o servidor!', 'error')

    return redirect(url_for('main.index'))
