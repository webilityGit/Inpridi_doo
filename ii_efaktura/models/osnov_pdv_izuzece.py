# Copyright 2022 Irvas International (http://www.irvas.rs)
# @author: Ljubisa Jovev <ljubisa.jovev@irvas.rs>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


# Tefaktura MNF strazi da se u slucaju specifikacije oslobadjanja placanja poreza
# pored kategorije , navede i razlog oslobodjenja. Ovaj model uvodi tbelu poreskih kategorija sa mogucim razlozima

class osnov_za_izuzece(models.Model):
    _name = "osnov.pdv.izuzece"
    _description = "Nomenklatura osnova za PDV izucece"
    _order = "unece_categ_id, code"

    code = fields.Char(required=True, string = "Šifra osnova", copy=False)  # ovde ide sifra izuzeca
    name = fields.Char(required=True, copy=False)  # Naziv izuzeca
    unece_categ_id = fields.Many2one(
        "unece.code.list",
        string="PDV kategorija",
        domain=[("type", "=", "tax_categ")],
        ondelete="restrict",
        help="Select the Tax Category Code of the official "
             "nomenclature of the United Nations Economic "
             "Commission for Europe (UNECE), DataElement 5305",
    )
    description = fields.Text()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "unece_categ_id_code_uniq",
            "unique(unece_categ_id, code)",
            "Kombinacija PDV osnov i kategorija PDV vec postoji",
        )
    ]

    @api.depends("code", "name")
    def name_get(self):
        res = []
        for entry in self:
            res.append((entry.id, "[{}] {}".format(entry.code, entry.name)))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=80):
        if args is None:
            args = []
        if name and operator == "ilike":
            recs = self.search([("code", "=", name)] + args, limit=limit)
            if recs:
                return recs.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)
