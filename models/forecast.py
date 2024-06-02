from odoo import models, fields, api

class ForecastedQty(models.Model):
    _name = 'mps.forecasted.qty'
    _description = 'Forecasted Quantity'

    name = fields.Char(string="Nom", readonly=True)
    quantity = fields.Float(string='Quantity')
    date_start = fields.Date(string='Date debut')
    date_end = fields.Date(string='Date de fin')
    starting_inventory_qty = fields.Float(string="Starting Inventory Quantity", compute='_compute_starting_inventory_qty')
    actual_demand_qty = fields.Float(string="Actual Demand Quantity", compute='_compute_actual_demand_qty')

    mps_id = fields.Many2one('mps', string="Master Production Schedule", ondelete='cascade')

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
                record.actual_demand_qty = sum(d.line.product_uom_qty for d in demand)
            else:
                record.actual_demand_qty = 0