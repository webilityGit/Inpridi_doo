from odoo import api,fields,models

class IIPdvExemptionReason(models.Model):
    _name = "ii.pdv.exemption.reason"
    _description = "Osnov za izuzece od PDV-a"
    _order = "category_id, code"

    code = fields.Char(string="Sifra osnova", required=True)
    name = fields.Char(string="Naziv osnova", required=True)
    category_id = fields.Many2one(
        "ii.pdv.category", string="PDV kategorija", required=True, ondelete="cascade"
    )
    description = fields.Text(string="Opis")
    active = fields.Boolean(default=True)