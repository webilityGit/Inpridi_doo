from . import models
from . import wizard
from odoo import api


def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import UserError
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if server_serie != '17.0':
        raise UserError(('This module support Odoo Version 17.0 only and found ' + server_serie))
    return True


def post_init_hook(env):
    companies = env['res.company'].search([])

    for company in companies:
        env['journal.setup.effective'].sudo().create({
            'company_id': company.id,
            'name': 'Default Effective Stock Journal',
        })

