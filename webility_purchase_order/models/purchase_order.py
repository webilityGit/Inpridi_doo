from odoo import models, fields

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    product_code = fields.Char(
        'Vendor Product Code',
        help="This vendor's product code will be used when printing a request for quotation. Keep empty to use the internal one.",compute='_compute_product_code')

    def _compute_product_code(self):
        for rec in self:
            rec.product_code = ''
            for res in rec.product_id.seller_ids:
                if rec.order_id.partner_id.id == rec.partner_id.id:
                    rec.product_code = res.product_code