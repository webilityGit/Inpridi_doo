from odoo import models, fields,api

class PurchaseOrderLineInherit(models.Model):
    _inherit = 'purchase.order.line'

    product_code = fields.Char(
        'Part number #',
        help="This vendor's product code will be used when printing a request for quotation. Keep empty to use the internal one.",compute='_compute_product_code')
    @api.onchange('order_id.partner_id','order_id.order_line.product_id')
    def _compute_product_code(self):
        for rec in self:
            rec.product_code = ''
            for vendor in rec.product_id.seller_ids:
                if rec.order_id.partner_id.id == vendor.partner_id.id:
                    rec.product_code = vendor.product_code