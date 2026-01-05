from odoo import models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Sekcija na FINALNOJ fakturi
    def _prepare_down_payment_section_line(self, **optional_values):
        vals = super()._prepare_down_payment_section_line(**optional_values)
        vals["name"] = _("Avansna uplata")
        return vals

    # Linija na AVANSNOJ fakturi
    def _prepare_down_payment_line_values(self, product, amount, **optional_values):
        vals = super()._prepare_down_payment_line_values(product, amount, **optional_values)
        vals["name"] = _("Avansna uplata")
        return vals