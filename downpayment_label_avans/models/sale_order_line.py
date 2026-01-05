# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.tools.misc import format_date


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_downpayment_description(self):
        """
        Override default 'Down Payment ...' label with Serbian 'Avansna uplata ...'
        for both section line and the auto-generated down payment line.
        """
        self.ensure_one()

        # For section lines (display_type == 'line_section' / 'line_note')
        if self.display_type:
            return _("Avansna uplata")

        dp_state = self._get_downpayment_state()
        name = _("Avansna uplata")

        if dp_state == "draft":
            name = _(
                "Avansna uplata: %(date)s (U pripremi)",
                date=format_date(self.env, self.create_date.date()),
            )
        elif dp_state == "cancel":
            name = _("Avansna uplata (Stornirano)")
        else:
            invoice = self._get_invoice_lines().filtered(
                lambda aml: aml.quantity >= 0
            ).move_id.filtered(lambda move: move.move_type == "out_invoice")

            if len(invoice) == 1 and invoice.payment_reference and invoice.invoice_date:
                name = _(
                    "Avansna uplata (ref: %(reference)s on %(date)s)",
                    reference=invoice.payment_reference,
                    date=format_date(self.env, invoice.invoice_date),
                )

        return name
