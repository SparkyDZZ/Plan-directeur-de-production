from odoo import models, fields, api

class ForecastedQty(models.Model):
    _name = 'mps.forecasted.qty'
    _description = 'Forecasted Quantity'

    name = fields.Char(string="Nom", readonly=True)
    quantity = fields.Float(string='Quantity')
    date = fields.Date(string='Date')
    period_id = fields.Many2one('mps.period', string="Période", required=True)
    starting_inventory_qty = fields.Float(string="Starting Inventory Quantity", compute='_compute_starting_inventory_qty')

    mps_id = fields.Many2one('mps', string="Master Production Schedule")

    @api.depends('mps_id', 'date')
    def _compute_starting_inventory_qty(self):
        for record in self:
            previous_inventory = self.search([
                ('mps_id', '=', record.mps_id.id),
                ('date', '<', record.date)
            ], order='date desc', limit=1)
            record.starting_inventory_qty = previous_inventory.quantity if previous_inventory else 0.0