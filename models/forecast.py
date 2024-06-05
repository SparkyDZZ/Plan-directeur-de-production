from odoo import models, fields, api
from datetime import datetime, timedelta

class ForecastedQty(models.Model):
    _name = 'mps.forecasted.qty'
    _description = 'Forecasted Quantity'

    name = fields.Char(string="Nom", readonly=True)
    forecast_qty = fields.Float(string='Quantity', default=0)
    date_start = fields.Date(string='Date debut')
    date_end = fields.Date(string='Date de fin')
    procurement_launched = fields.Boolean(string="Le réapprovisionnement a été lancé pour cette estimation", default=False)
    replenish_qty = fields.Float(string="A réapprovisionner", default=0)
    replenish_qty_updated = fields.Boolean(string="Replenish_qty a été mise à jour manuellement", default=False)
    starting_inventory_qty = fields.Float(string="Starting Inventory Quantity", comput="_compute_starting_inventory_qty", store=False)
    actual_demand_qty = fields.Float(string="Actual Demand Quantity", compute='_compute_actual_demand_qty', store=False)
    actual_demand_qty_y2 = fields.Float(string="Demande Année-2", compute='_compute_actual_demand_qty_y2', store=False)
    actual_demand_qty_y1 = fields.Float(string="Demande Année-1", compute='_compute_actual_demand_qty_y1', store=False)

    mps_id = fields.Many2one('mps', string="Master Production Schedule", required=True, ondelete='cascade')

    @api.depends('date_start', 'date_end', 'mps_id')
    def _compute_starting_inventory_qty(self):
        for record in self:
            previous_period = self.search([
                ('mps_id', '=', record.mps_id.id),
                ('date_end', '<', record.date_start),
            ], order='date_end desc', limit=1)
            if previous_period:
                record.starting_inventory_qty = previous_period.quantity
            else:
                record.starting_inventory_qty = 0

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
                for d in demand:
                    print(d.order_id.id)

            else:
                record.actual_demand_qty = 0

    @api.depends('date_start', 'date_end', 'mps_id')
    def _compute_actual_demand_qty_y2(self):
        for record in self:
            if record.mps_id and record.date_start and record.date_end:
                y2_start = record.date_start - timedelta(days=365 * 2)
                y2_end = record.date_end - timedelta(days=365 * 2)
                demand_y2 = self.env['sale.order.line'].search([
                    ('product_id', '=', record.mps_id.product_id.id),
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('order_id.date_order', '>=', y2_start),
                    ('order_id.date_order', '<=', y2_end)
                ])
                record.actual_demand_qty_y2 = sum(d.product_uom_qty for d in demand_y2)
            else:
                record.actual_demand_qty_y2 = 0

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
        if production_schedule:
            production_schedule.write({'replenish_qty': replenish_qty})
            return True
        return False