from odoo import api, fields, models

class IIPdvCategory(models.Model):
    _name = "ii.pdv.category"
    _description = "PDV Kategorija"
    _order = "code"

    code = fields.Char(string="Sifra kategorije", required=True)
    name = fields.Char(string="Naziv kategorije", required=True)
    description = fields.Text(default="Opis")
    active = fields.Boolean(default=True)
    exemption_reason_ids = fields.One2many(
        "ii.pdv.exemption.reason", "category_id", string="Razlozi izuzeca"
    )