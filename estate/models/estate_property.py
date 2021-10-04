from odoo import fields,models,api
from datetime import datetime,date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError,ValidationError

class EstateProperty(models.Model):
	_name = "estate.property"
	_description = "The Real Estate Advertisement Module" 
	_order = "id desc"
	
	property_type_ids = fields.Many2one('estate.property.type', required=True)
	buyer = fields.Many2one('res.partner',required=True, copy=False)
	salesperson = fields.Many2one('res.users', string="Salesperson", required=True, default=lambda self: self.env.user)
	tags_ids = fields.Many2many('estate.property.tag',string="tags")
	offer_ids = fields.One2many('estate.property.offer','partner_id', string="offer")
	description = fields.Text()
	postcode = fields.Char(string="Postcode")
	date_availability = fields.Date(string="Available From", default=datetime.today() + relativedelta(months=+3), copy=False)
	selling_price = fields.Float(string="Selling Price",default=0.00, readonly=True, copy=False)
	bedrooms = fields.Integer(default=2, string="Bedrooms")
	living_area = fields.Integer(string="Living Area(sqm)")
	facades = fields.Integer()
	garage = fields.Boolean(default=False)
	garden = fields.Boolean(default=False)
	garden_area = fields.Integer(string="Garden Area(sqm)")
	garden_orientation = fields.Selection(
		string='Garden Orientation',
		selection=[('North','North'),('South','South'),('East','East'),('West','West')])
	active = fields.Boolean()
	total_area = fields.Float(compute="_total_area",string="Total Area (sqm)")
	best_price = fields.Many2one('estate.property.offer', compute="_best_price", string="Best Offer")
	partner_names = fields.Char(compute="_compute_description", string="Buyer Names")
	model_id = fields.Many2one('estate.property.type')
	name = fields.Char(required=True, string="Title")
	expected_price = fields.Float(required=True, string="Expected Price")
	state = fields.Selection(
		
		required=True,
		copy=False,
		selection=[
		('New', 'New'),
		('Offer Received', 'Offer Received'),
		('Offer Accepted', 'Offer Accepted'),
		('Sold', 'Sold'),
		('Canceled','Canceled')],
		state='State', default='New')




	_sql_constraints = [
		('expected_price','CHECK(expected_price >0)','A property expected price must be strictly positive'),
		('selling_price','CHECK(selling_price > 0)', 'A property selling price must be strictly positve'),
		('selling_price','CHECK(selling_price >= expected_price/90)','The offer should always be 90 percentage of the expected price.')
		
	]
	
	
	# @api.constrains('selling_price')
	# def _check_constrains(self):
		# expected_price_percentage = self.expected_price/90
	# 	for record in self:
			
			# if record.selling_price < expected_price_percentage :
				# raise ValidationError("this offer cannot be accepted, an offer must be 90%")	

	
	
	
	@api.onchange('garden')
	def _onchange_garden_area(self):
		if self.garden == True:
			self.garden_area = 10
			self.garden_orientation = "North"
		if self.garden == False:
			self.garden_area = ''
			self.garden_orientation = ''
		
		
	
	# @api.depends("offer_ids")
	# def _best_price(self):
	# 	price_price = self.env['offer_ids'].search([])
	# 	best_price_calcutation = max(price_price.mapped('price'))

	# 	for record in self:
	# 		record.best_price = best_price_calculation
	# 		print(best_price)
			
	 	
	
		
	@api.depends('living_area', 'garden_area')
	def _total_area(self):
		for t in self:
			t.total_area = t.living_area + t.garden_area

	
	def action_sold(self):
		for record in self:
			if record.state == "Canceled":
				raise UserError("Canceled properties cannot be sold")
			else:
				record.state = "Sold"
			

	def action_cancel(self):
		for record in self:
			if record.state == "Sold":
				raise UserError("Sold properties cannot be canceled")
			else:
				record.state = "Canceled"



class EstatePropertyType(models.Model):
	_name = "estate.property.type"
	_order=	"name"
	
	name = fields.Char(required=True, string="Title")
	
	property_type = fields.Selection(
		string= "Property Type",
		selection=[
			('House','House'),
			('Apartment','Apartment'),
			('Penthouse','Penthouse'),
			('Castle','Castle'),('Cottage','Cottage')])
	
	
	property_ids = fields.One2many('estate.property','model_id')
	sequence = fields.Integer('Sequence',default=1, help="Used to order stages. Lower is better.")

	_sql_constraints =[
		('property_type_unique','unique(property_type)','Property type name should be unique'),
	]


	
	

	

class EstatePropertyTag(models.Model):
	_name = "estate.property.tag"
	_order = "name"
  
  
	name = fields.Char(string="name")
	tag_list = fields.Selection(
		selection=[('cozy','cozy'),('renovated','renovated')])

	color = fields.Integer('color index')

	_sql_constraints=[
		('tag_list_unique','unique(tag_list)','A property tag name should be unique'),
		
	]  
	  
	  
class EstatePropertyOffer(models.Model):
	# _inherit = "estate.property"
	_name = "estate.property.offer"
	_order = "price desc"
	
	
	name = fields.Char(string="Offer")
	price = fields.Float(string="Price (USD)")
	status = fields.Selection(copy=False,
		selection = [('Refused','Refused'),('Accepted','Accepted')]
	)
	partner_id = fields.Many2one('res.partner', string="Partner", required=True)
	property_id = fields.Many2one('estate.property', required=False)
	validity = fields.Integer(default=7, string="Validity (days)")
	date_deadline = fields.Date(string="Deadline", readonly=False)
	# buyer_ids = fields.Many2one('estate.property', string='Buyer_ids')
	# buyer = fields.Float(related='buyer_ids', string='Buyer')
	# selling_price_ids = fields.Many2one('estate.property', string='selling_price_ids')
	# selling_price = fields.Float(related='selling_price_ids', string='Selling Price')



	_sql_constraints=[
		('price','Check(price > 0)', 'An offer price must be strictly positve')
	]



	# @api.depends('validity','create_date')
	# def _deadline(self):
	# 	for d in self:
	# 		d.deadline = d.timedelta(days='validity') + d.self.env['estate.property.offer'].search('price')
	# 	return deadline
	


	
	@api.model
	def create(self,vals):
		value = super(EstatePropertyOffer,self).create(vals)
		value.write({'date_deadline':value.create_date + timedelta(days=vals.get('validity'))})
		return value

	@api.model
	def write(self,vals):
		value = super(EstatePropertyOffer,self).write(vals)
		# value.write({'date_deadline':value.create_date + timedelta(days=vals.get('validity'))})
		# value = super(EstatePropertyOffer,self).write(vals)
		# value.write({'date_deadline':value.create_date + timedelta(days=vals.get('validity'))})
		return value

   
	def action_accept(self):
				
		for record in self:
			if record.status == "Accepted":
				raise UserError("Only one offer can be accepted for a given property")
				
			if record.status == "Refused":
				record.status = "Accepted"
				
	
	def action_refuse(self):
		for record in self:
			if record.status == "Accepted":
				record.status = "Refused"
	
	 
	# @api.onchange('selling_price_ids')
	# def _onchange_selling_price(self,selling_price_ids):
	# 	for r in self:
	# 		if r.status == 'Accepted':
	# 			r.selling_price_ids = self.price
	# 			# self.buyer_ids = record.partner_id

	
	
