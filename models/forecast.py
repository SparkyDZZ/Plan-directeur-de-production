from odoo import models, fields, api
from datetime import datetime, timedelta
import pdb

class ForecastedQty(models.Model):
    _name = 'mps.forecasted.qty'
    _description = 'Forecasted Quantity'

    name = fields.Char(string="Nom", readonly=True)
    forecast_qty = fields.Float(string='Quantity', default=0.0)
    date_start = fields.Date(string='Date debut')
    date_end = fields.Date(string='Date de fin')
    procurement_launched = fields.Boolean(string="Le réapprovisionnement a été lancé pour cette estimation", default=False)
    replenish_qty = fields.Float(string="A réapprovisionner", compute="_compute_replenish_qty", default=0.0, store=True)
    old_replenish_qty = fields.Float(string="Nouvelle qty de réapprovisionnement")
    replenish_qty_updated = fields.Boolean(string="Replenish_qty a été mise à jour manuellement", default=False)
    starting_inventory_qty = fields.Float(string="Starting Inventory Quantity", compute="_compute_starting_inventory_qty")
    safety_stock_qty = fields.Float(string="Forecasted Stock", compute="_compute_safety_stock_qty", default=0.0)
    actual_demand_qty = fields.Float(string="Actual Demand Quantity", compute='_compute_actual_demand_qty')
    actual_demand_qty_y1 = fields.Float(string="Demande Année-1", compute='_compute_actual_demand_qty_y1')
    indirect_demand_forecast = fields.Float(string="Prévision de la demande indirecte", compute="_compute_indirect_demand")

    mps_id = fields.Many2one('mps', string="Master Production Schedule", required=True, ondelete='cascade')

    @api.depends('date_start', 'date_end', 'mps_id')
    def _compute_starting_inventory_qty(self):
        for record in self:
            previous_period = self.search([
                ('mps_id', '=', record.mps_id.id),
                ('date_end', '<', record.date_start),
            ], order='date_end desc', limit=1)
            if previous_period:
                record.starting_inventory_qty = previous_period.safety_stock_qty
            else:
                stock_quant = self.env['stock.quant'].search([
                    ('product_id', '=', record.mps_id.product_id.id),
                    ('location_id', 'child_of', record.mps_id.warehouse_id.lot_stock_id.id),
                ], limit=1)
                record.starting_inventory_qty = stock_quant.quantity if stock_quant else 0

    @api.depends('mps_id', 'starting_inventory_qty', 'replenish_qty', 'forecast_qty', 'indirect_demand_forecast')
    def _compute_safety_stock_qty(self):
        for record in self:
            record.safety_stock_qty = record.starting_inventory_qty + record.replenish_qty - record.forecast_qty - record.indirect_demand_forecast

    @api.depends('date_start', 'date_end', 'mps_id')
    def _compute_actual_demand_qty(self):
        for record in self:
            if record.mps_id and record.date_start and record.date_end:
                demand = self.env['sale.order.line'].search([
                    ('product_id', '=', record.mps_id.product_id.id),
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('order_id.date_order', '>=', record.date_start),
                    ('order_id.date_order', '<=', record.date_end)
                ])
                record.actual_demand_qty = sum(d.product_uom_qty for d in demand)
            else:
                record.actual_demand_qty = 0

    @api.depends('date_start', 'date_end', 'mps_id')
    def _compute_actual_demand_qty_y1(self):
        for record in self:
            if record.mps_id and record.date_start and record.date_end:
                y1_start = record.date_start - timedelta(days=365)
                y1_end = record.date_end - timedelta(days=365)
                demand_y1 = self.env['sale.order.line'].search([
                    ('product_id', '=', record.mps_id.product_id.id),
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('order_id.date_order', '>=', y1_start),
                    ('order_id.date_order', '<=', y1_end)
                ])
                record.actual_demand_qty_y1 = sum(d.product_uom_qty for d in demand_y1)
            else:
                record.actual_demand_qty_y1 = 0

    @api.depends('date_start', 'date_end', 'mps_id')
    def _compute_indirect_demand(self):
        for record in self:
            if record.mps_id and record.mps_id.has_indirect_demand:
                parent_mps = self.env['mps'].search([
                    ('bom_id.bom_line_ids.product_id', '=', record.mps_id.product_id.id),
                    ('warehouse_id', '=', record.mps_id.warehouse_id.id)
                ], limit=1)

                if parent_mps:
                    bom_line = self.env['mrp.bom.line'].search([
                        ('bom_id', '=', parent_mps.bom_id.id),
                        ('product_id', '=', record.mps_id.product_id.id)
                    ], limit=1)

                    if bom_line:
                        record.indirect_demand_forecast = parent_mps.forecast_ids.filtered(lambda f: f.date_start == record.date_start).replenish_qty * bom_line.product_qty
                    else:
                        record.indirect_demand_forecast = 0
                else:
                    record.indirect_demand_forecast = 0
            else:
                record.indirect_demand_forecast = 0

    @api.depends('forecast_qty', 'starting_inventory_qty', 'safety_stock_qty', 'indirect_demand_forecast','mps_id.max_to_replenish_qty', 'mps_id.forecast_target_qty', 'mps_id.min_to_replenish_qty','replenish_qty_updated')
    def _compute_replenish_qty(self):
        for record in self:
            if not record.replenish_qty_updated:
                min_qty = record.mps_id.min_to_replenish_qty
                max_qty = record.mps_id.max_to_replenish_qty
                replenish_needed = record.forecast_qty + record.mps_id.forecast_target_qty - record.starting_inventory_qty + record.indirect_demand_forecast
                if replenish_needed > max_qty:
                    record.replenish_qty = max_qty
                    record.old_replenish_qty = max_qty
                elif replenish_needed < min_qty:
                    record.replenish_qty = min_qty
                    record.old_replenish_qty = min_qty
                else:
                    record.replenish_qty = replenish_needed
                    record.old_replenish_qty = replenish_needed

            else:
                record.replenish_qty = record.old_replenish_qty
            print(f"{record.mps_id.display_name} : {record.replenish_qty}")

    @api.model
    def create(self, vals):
        res = super(ForecastedQty, self).create(vals)
        res._compute_replenish_qty()
        return res

    @api.model
    def write(self, vals):
        res = super(ForecastedQty, self).write(vals)
        return res
        
    @api.model
    def set_forecast_qty(self, production_schedule_id, forecast_qty):
        production_schedule = self.browse(production_schedule_id)
        if production_schedule:
            production_schedule.write({'forecast_qty': forecast_qty})
            return True
        return False

    @api.model
    def set_replenish_qty(self, production_schedule_id, replenish_qty):
        production_schedule = self.browse(production_schedule_id)
        if production_schedule.exists():
            production_schedule.write({'old_replenish_qty': replenish_qty, 'replenish_qty_updated': True})
            return True
        return False

    @api.model
    def set_procurement_launched(self, production_schedule_id):
        production_schedule = self.browse(production_schedule_id)
        if production_schedule:
            production_schedule.write({'procurement_launched': True})
            return True
        return False

    @api.model
    def remove_replenish_qty(self, production_schedule_id):
        production_schedule = self.browse(production_schedule_id)
        if production_schedule:
            production_schedule.write({'replenish_qty': production_schedule.old_replenish_qty, 'replenish_qty_updated': False})
            return True
        return False
