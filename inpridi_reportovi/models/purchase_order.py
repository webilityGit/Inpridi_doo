from odoo import models, fields, api

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    product_code = fields.Char('Part number #', compute='_compute_product_code', store=False)

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_product_code(self):
        for rec in self:
            code = rec.product_id.default_code or ''
            partner = rec.order_id.partner_id
            if rec.product_id and partner:
                for seller in rec.product_id.seller_ids:
                    if seller.partner_id == partner and seller.product_code:
                        code = seller.product_code
                        break
            rec.product_code = code
