from odoo import models, fields

class Period(models.Model):
    _name = 'mps.period'
    _description = 'Period'

    name = fields.Char(string='Name')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')