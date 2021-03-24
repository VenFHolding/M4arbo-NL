from odoo import fields, models
from datetime import datetime, timedelta


class WebsitePloicy(models.Model):
    _name = "custom.website.policy"
    _description='Website Policy Details'

    company_covid_policy = fields.Html('Privacy Policy', required=True)
