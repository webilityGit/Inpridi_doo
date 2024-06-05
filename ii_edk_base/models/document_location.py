# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar

from collections import defaultdict, OrderedDict
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare


class Location(models.Model):
    _name = "archive.location"
    _description = "Document Locations"
    _parent_name = "location_id"
    _parent_store = True
    _order = 'complete_name, id'
    _rec_name = 'complete_name'
    _rec_names_search = ['complete_name', 'barcode']
    _check_company_auto = True

    @api.model
    def default_get(self, fields):
        res = super(Location, self).default_get(fields)
        if 'barcode' in fields and 'barcode' not in res and res.get('complete_name'):
            res['barcode'] = res['complete_name']
        return res

    name = fields.Char('Location Name', required=True)
    # complete_name = fields.Char("Full Location Name")
    complete_name = fields.Char("Full Location Name", compute='_compute_complete_name', recursive=True, store=True)
    active = fields.Boolean('Active', default=True, help="By unchecking the active field, you may hide a location without deleting it.")
    usage = fields.Selection([

        ('view', 'View'),
        ('internal', 'Internal Location'),
        ('inventory', 'Inventory Loss'),
        ('transit', 'Transit Location')], string='Location Type',
        default='internal', index=True, required=True,
        help="* Vendor Location: Virtual location representing the source location for products coming from your vendors"
             "\n* View: Virtual location used to create a hierarchical structures for your warehouse, aggregating its child locations ; can't directly contain products"
             "\n* Internal Location: Physical locations inside your own warehouses,"
             "\n* Customer Location: Virtual location representing the destination location for products sent to your customers"
             "\n* Inventory Loss: Virtual location serving as counterpart for inventory operations used to correct stock levels (Physical inventories)"

            )
    location_id = fields.Many2one(
        'archive.location', 'Parent Location', index=True, ondelete='cascade', check_company=True,
        help="The parent location that includes this location. Example : The 'Dispatch Zone' is the 'Gate 1' parent location.")
    child_ids = fields.One2many('archive.location', 'location_id', 'Contains')
    child_internal_location_ids = fields.Many2many(
        'archive.location',
        string='Internal locations among descendants',
        compute='_compute_child_internal_location_ids',
        recursive=True,
        help='This location (if it\'s internal) and all its descendants filtered by type=Internal.'
    )
    comment = fields.Html('Additional Information')
    posx = fields.Integer('Corridor (X)', default=0, help="Optional localization details, for information purpose only")
    posy = fields.Integer('Shelves (Y)', default=0, help="Optional localization details, for information purpose only")
    posz = fields.Integer('Height (Z)', default=0, help="Optional localization details, for information purpose only")
    parent_path = fields.Char(index=True, unaccent=False)
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company, index=True,
        help='Let this field empty if this location is shared between companies')
    scrap_location = fields.Boolean('Is a Scrap Location?', default=False, help='Check this box to allow using this location to put scrapped/damaged goods.')



    barcode = fields.Char('Barcode', copy=False)

    cyclic_inventory_frequency = fields.Integer("Inventory Frequency (Days)", default=0, help=" When different than 0, inventory count date for products stored at this location will be automatically set at the defined frequency.")
    last_inventory_date = fields.Date("Last Effective Inventory", readonly=True, help="Date of the last inventory at this location.")
    next_inventory_date = fields.Date("Next Expected Inventory", compute="_compute_next_inventory_date", store=True, help="Date for next planned inventory based on cyclic schedule.")
 #   warehouse_view_ids = fields.One2many('stock.warehouse', 'view_location_id', readonly=True)
 #   warehouse_id = fields.Many2one('stock.warehouse', compute='_compute_warehouse_id', store=True)
  #  storage_category_id = fields.Many2one('stock.storage.category', string='Storage Category', check_company=True)
  #  outgoing_move_line_ids = fields.One2many('stock.move.line', 'location_id') # used to compute weight
  #  incoming_move_line_ids = fields.One2many('stock.move.line', 'location_dest_id') # used to compute weight
 #   net_weight = fields.Float('Net Weight', compute="_compute_weight")
  #  forecast_weight = fields.Float('Forecasted Weight', compute="_compute_weight")

    _sql_constraints = [('barcode_company_uniq', 'unique (barcode,company_id)', 'The barcode for a location must be unique per company !'),
                        ('inventory_freq_nonneg', 'check(cyclic_inventory_frequency >= 0)', 'The inventory frequency (days) for a location must be non-negative')]

    # @api.depends('outgoing_move_line_ids.reserved_qty', 'incoming_move_line_ids.reserved_qty',
    #              'outgoing_move_line_ids.state', 'incoming_move_line_ids.state',
    #              'outgoing_move_line_ids.product_id.weight', 'outgoing_move_line_ids.product_id.weight',
    #              'quant_ids.quantity', 'quant_ids.product_id.weight')
    # @api.depends_context('exclude_sml_ids')
    # def _compute_weight(self):
    #     for location in self:
    #         location.net_weight = 0
    #         quants = location.quant_ids.filtered(lambda q: q.product_id.type != 'service')
    #         excluded_sml_ids = self._context.get('exclude_sml_ids', [])
    #         incoming_move_lines = location.incoming_move_line_ids.filtered(lambda ml: ml.product_id.type != 'service' and ml.state not in ['draft', 'done', 'cancel'] and ml.id not in excluded_sml_ids)
    #         outgoing_move_lines = location.outgoing_move_line_ids.filtered(lambda ml: ml.product_id.type != 'service' and ml.state not in ['draft', 'done', 'cancel'] and ml.id not in excluded_sml_ids)
    #         for quant in quants:
    #             location.net_weight += quant.product_id.weight * quant.quantity
    #         location.forecast_weight = location.net_weight
    #         for line in incoming_move_lines:
    #             location.forecast_weight += line.product_id.weight * line.reserved_qty
    #         for line in outgoing_move_lines:
    #             location.forecast_weight -= line.product_id.weight * line.reserved_qty

    @api.depends('name', 'location_id.complete_name', 'usage')
    def _compute_complete_name(self):
        for location in self:
            if location.location_id and location.usage != 'view':
                location.complete_name = '%s/%s' % (location.location_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    @api.depends('cyclic_inventory_frequency', 'last_inventory_date', 'usage', 'company_id')
    def _compute_next_inventory_date(self):
        for location in self:
            if location.company_id and location.usage in ['internal', 'transit'] and location.cyclic_inventory_frequency > 0:
                try:
                    if location.last_inventory_date:
                        days_until_next_inventory = location.cyclic_inventory_frequency - (fields.Date.today() - location.last_inventory_date).days
                        if days_until_next_inventory <= 0:
                            location.next_inventory_date = fields.Date.today() + timedelta(days=1)
                        else:
                            location.next_inventory_date = location.last_inventory_date + timedelta(days=location.cyclic_inventory_frequency)
                    else:
                        location.next_inventory_date = fields.Date.today() + timedelta(days=location.cyclic_inventory_frequency)
                except OverflowError:
                    raise UserError(_("The selected Inventory Frequency (Days) creates a date too far into the future."))
            else:
                location.next_inventory_date = False

   # @api.depends('warehouse_view_ids', 'location_id')
   # def _compute_warehouse_id(self):
   #     warehouses = self.env['stock.warehouse'].search([('view_location_id', 'parent_of', self.ids)])
   #     warehouses = warehouses.sorted(lambda w: w.view_location_id.parent_path, reverse=True)
   #     view_by_wh = OrderedDict((wh.view_location_id.id, wh.id) for wh in warehouses)
   #     self.warehouse_id = False
   #     for loc in self:
   #         if not loc.parent_path:
   #             continue
   #         path = set(int(loc_id) for loc_id in loc.parent_path.split('/')[:-1])
   #         for view_location_id in view_by_wh:
   #             if view_location_id in path:
   #                 loc.warehouse_id = view_by_wh[view_location_id]
   #                 break

    @api.depends('child_ids.usage', 'child_ids.child_internal_location_ids')
    def _compute_child_internal_location_ids(self):
        # batch reading optimization is not possible because the field has recursive=True
        for loc in self:
            loc.child_internal_location_ids = self.search([('id', 'child_of', loc.id), ('usage', '=', 'internal')])

    @api.onchange('usage')
    def _onchange_usage(self):
        if self.usage not in ('internal', 'inventory'):
            self.scrap_location = False




    def write(self, values):
        if 'company_id' in values:
            for location in self:
                if location.company_id.id != values['company_id']:
                    raise UserError(_("Changing the company of this record is forbidden at this point, you should rather archive it and create a new one."))
        if 'usage' in values and values['usage'] == 'view':
            if self.mapped('quant_ids'):
                raise UserError(_("This location's usage cannot be changed to view as it contains products."))
        if 'usage' in values or 'scrap_location' in values:
            modified_locations = self.filtered(
                lambda l: any(l[f] != values[f] if f in values else False
                              for f in {'usage', 'scrap_location'}))


        # if 'active' in values:
        #     if values['active'] == False:
        #         for location in self:
        #             warehouses = self.env['stock.warehouse'].search([('active', '=', True), '|', ('lot_stock_id', '=', location.id), ('view_location_id', '=', location.id)])
        #             if warehouses:
        #                 raise UserError(_("You cannot archive the location %s as it is"
        #                 " used by your warehouse %s") % (location.display_name, warehouses[0].display_name))
        #


        res = super(Location, self).write(values)
    #    self.invalidate_model(['warehouse_id'])
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
    #    self.invalidate_model(['warehouse_id'])
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % self.name
        return super().copy(default=default)



    def _get_next_inventory_date(self):
        """ Used to get the next inventory date for a quant located in this location. It is
        based on:
        1. Does the location have a cyclic inventory set?
        2. If not 1, then is there an annual inventory date set (for its company)?
        3. If not 1 and 2, then quants have no next inventory date."""
        if self.usage not in ['internal', 'transit']:
            return False
        next_inventory_date = False
        if self.next_inventory_date:
            next_inventory_date = self.next_inventory_date
        elif self.company_id.annual_inventory_month:
            today = fields.Date.today()
            annual_inventory_month = int(self.company_id.annual_inventory_month)
            # Manage 0 and negative annual_inventory_day
            annual_inventory_day = max(self.company_id.annual_inventory_day, 1)
            max_day = calendar.monthrange(today.year, annual_inventory_month)[1]
            # Manage annual_inventory_day bigger than last_day
            annual_inventory_day = min(annual_inventory_day, max_day)
            next_inventory_date = today.replace(
                month=annual_inventory_month, day=annual_inventory_day)
            if next_inventory_date <= today:
                # Manage leap year with the february
                max_day = calendar.monthrange(today.year + 1, annual_inventory_month)[1]
                annual_inventory_day = min(annual_inventory_day, max_day)
                next_inventory_date = next_inventory_date.replace(
                    day=annual_inventory_day, year=today.year + 1)
        return next_inventory_date









