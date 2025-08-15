# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_is_zero
from bisect import bisect_left
from collections import defaultdict
import re
from .selection import (DocumentGroupType)

ACCOUNT_REGEX = re.compile(r'(?:(\S*\d+\S*))?(.*)')
ACCOUNT_CODE_REGEX = re.compile(r'^[A-Za-z0-9.]+$')

class KategorijeArhivskeGradje(models.Model):
    _name = "ii.edk.lista.kag"
    _inherit = ['mail.thread']
    _description = "Lista kategorija arhivske građe i dokumentarnog materijala"
    _order = "code, company_id"
    _check_company_auto = True

    name = fields.Char(string="Category Name", required=True, index='trigram', tracking=True)

    code = fields.Char(size=64, required=True, tracking=True)
    deprecated = fields.Boolean(default=False, tracking=True)
    used = fields.Boolean(compute='_compute_used', search='_search_used')

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)

    group_id = fields.Many2one('ii.edk.lista.gkag', compute='_compute_category_group', store=True, readonly=True,
                               help="Group prefixes can determine category groups.")
    root_id = fields.Many2one('document.category.root', compute='_compute_category_root', store=True)
    klasifikaciona_oznaka = fields.Char(
        string='Classification tag',
    )
    rok_cuvanja_meseci = fields.Integer(
        string='Storage Period in mounths',
        required=True,
    )
    napomena = fields.Char(
        string='Note related to storage period', )

    rok_cuvanja_godina = fields.Char(
        string='Storage Period in years',
    )
    default_arh_pozicija = fields.Many2one("archive.location", "Predefinisana lokacija za rhoviranje")

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the account must be unique per company !')
    ]
    @api.onchange("rok_cuvanja_meseci")
    def _compute_rok_cuvanja(self):
        temp_tekst = " "
        if self.rok_cuvanja_meseci:
            temp_tekst = str(self.rok_cuvanja_meseci // 12) + " godina "

            if self.napomena:
                temp_tekst = temp_tekst + self.napomena
        self.rok_cuvanja_godina = temp_tekst
        return

    def _compute_used(self):
        ids = set(self._search_used('=', True)[0][2])
        for record in self:
            record.used = record.id in ids
    @api.depends('code')
    def _compute_category_group(self):
        if self.ids:
            self.env['ii.edk.lista.gkag']._adapt_category_for_category_groups(self)
        else:
            self.group_id = False

    @api.depends('code')
    def _compute_category_root(self):
        # this computes the first 2 digits of the account.
        # This field should have been a char, but the aim is to use it in a side panel view with hierarchy, and it's only supported by many2one fields so far.
        # So instead, we make it a many2one to a psql view with what we need as records.
        for record in self:
            record.root_id = (ord(record.code[0]) * 1000 + ord(record.code[1:2] or '\x00')) if record.code else False

    def action_read_document_category(self):
        self.ensure_one()
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ii.edk.lista.kag',
            'res_id': self.id,
        }

class GrupeKategorijeArhivskeGradje(models.Model):
    _name = "ii.edk.lista.gkag"
    _description = 'Lista Grupa kategorija arhivske građe i dokumentarnog materijala'
    _parent_store = True
    _order = 'code_prefix_start'

    parent_id = fields.Many2one('ii.edk.lista.gkag', index=True, ondelete='cascade', readonly=True)
    parent_path = fields.Char(index=True, unaccent=False)
    name = fields.Char(required=True)
    code_prefix_start = fields.Char()
    code_prefix_end = fields.Char()
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)

    _sql_constraints = [
        (
            'check_length_prefix',
            'CHECK(char_length(COALESCE(code_prefix_start, \'\')) = char_length(COALESCE(code_prefix_end, \'\')))',
            'The length of the starting and the ending code prefix must be the same'
        ),
    ]

    @api.onchange('code_prefix_start')
    def _onchange_code_prefix_start(self):
        if not self.code_prefix_end or self.code_prefix_end < self.code_prefix_start:
            self.code_prefix_end = self.code_prefix_start

    @api.onchange('code_prefix_end')
    def _onchange_code_prefix_end(self):
        if not self.code_prefix_start or self.code_prefix_start > self.code_prefix_end:
            self.code_prefix_start = self.code_prefix_end

    def name_get(self):
        result = []
        for group in self:
            prefix = group.code_prefix_start and str(group.code_prefix_start)
            if prefix and group.code_prefix_end != group.code_prefix_start:
                prefix += '-' + str(group.code_prefix_end)
            name = (prefix and (prefix + ' ') or '') + group.name
            result.append((group.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            criteria_operator = ['|'] if operator not in expression.NEGATIVE_TERM_OPERATORS else ['&', '!']
            domain = criteria_operator + [('code_prefix_start', '=ilike', name + '%'), ('name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.constrains('code_prefix_start', 'code_prefix_end')
    def _constraint_prefix_overlap(self):
        self.flush_model()
        query = """
            SELECT other.id FROM ii_edk_lista_gkag this
            JOIN ii_edk_lista_gkag other
              ON char_length(other.code_prefix_start) = char_length(this.code_prefix_start)
             AND other.id != this.id
             AND other.company_id = this.company_id
             AND (
                other.code_prefix_start <= this.code_prefix_start AND this.code_prefix_start <= other.code_prefix_end
                OR
                other.code_prefix_start >= this.code_prefix_start AND this.code_prefix_end >= other.code_prefix_start
            )
            WHERE this.id IN %(ids)s
        """
        self.env.cr.execute(query, {'ids': tuple(self.ids)})
        res = self.env.cr.fetchall()
        if res:
            raise ValidationError(_('Account Groups with the same granularity can\'t overlap'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'code_prefix_start' in vals and not vals.get('code_prefix_end'):
                vals['code_prefix_end'] = vals['code_prefix_start']
        res_ids = super(GrupeKategorijeArhivskeGradje, self).create(vals_list)
        res_ids._adapt_category_for_category_groups()
        res_ids._adapt_parent_category_groups()
        return res_ids

    def write(self, vals):
        res = super(GrupeKategorijeArhivskeGradje, self).write(vals)
        if 'code_prefix_start' in vals or 'code_prefix_end' in vals:
            self._adapt_category_for_category_groups()
            self._adapt_parent_category_groups()
        return res

    def unlink(self):
        for record in self:
            account_ids = self.env['ii.edk.lista.kag'].search([('group_id', '=', record.id)])
            account_ids.write({'group_id': record.parent_id.id})

            children_ids = self.env['ii.edk.lista.gkag'].search([('parent_id', '=', record.id)])
            children_ids.write({'parent_id': record.parent_id.id})
        super(GrupeKategorijeArhivskeGradje, self).unlink()

    def _adapt_category_for_category_groups(self, account_ids=None):
        """Ensure consistency between accounts and account groups.

        Find and set the most specific group matching the code of the account.
        The most specific is the one with the longest prefixes and with the starting
        prefix being smaller than the account code and the ending prefix being greater.
        """
        company_ids = account_ids.company_id.ids if account_ids else self.company_id.ids
        account_ids = account_ids.ids if account_ids else []
        if not company_ids and not account_ids:
            return
        self.flush_model()
        self.env['ii.edk.lista.kag'].flush_model()

        account_where_clause = ''
        where_params = [tuple(company_ids)]
        if account_ids:
            account_where_clause = 'AND account.id IN %s'
            where_params.append(tuple(account_ids))

        self._cr.execute(f'''
            WITH candidates_ii_edk_lista_gkags AS (
                SELECT
                    account.id AS account_id,
                    ARRAY_AGG(agroup.id ORDER BY char_length(agroup.code_prefix_start) DESC, agroup.id) AS group_ids
                FROM ii_edk_lista_kag account
                LEFT JOIN ii_edk_lista_gkag agroup
                    ON agroup.code_prefix_start <= LEFT(account.code, char_length(agroup.code_prefix_start))
                    AND agroup.code_prefix_end >= LEFT(account.code, char_length(agroup.code_prefix_end))
                    AND agroup.company_id = account.company_id
                WHERE account.company_id IN %s {account_where_clause}
                GROUP BY account.id
            )
            UPDATE ii_edk_lista_kag
            SET group_id = rel.group_ids[1]
            FROM candidates_ii_edk_lista_gkags rel
            WHERE ii_edk_lista_kag.id = rel.account_id
        ''', where_params)
        self.env['ii.edk.lista.kag'].invalidate_model(['group_id'])

    def _adapt_parent_category_groups(self):
        """Ensure consistency of the hierarchy of account groups.

        Find and set the most specific parent for each group.
        The most specific is the one with the longest prefixes and with the starting
        prefix being smaller than the child prefixes and the ending prefix being greater.
        """
        if not self:
            return
        self.flush_model()
        query = """
            WITH relation AS (
       SELECT DISTINCT FIRST_VALUE(parent.id) OVER (PARTITION BY child.id ORDER BY child.id, char_length(parent.code_prefix_start) DESC) AS parent_id,
                       child.id AS child_id
                  FROM ii_edk_lista_gkag parent
                  JOIN ii_edk_lista_gkag child
                    ON char_length(parent.code_prefix_start) < char_length(child.code_prefix_start)
                   AND parent.code_prefix_start <= LEFT(child.code_prefix_start, char_length(parent.code_prefix_start))
                   AND parent.code_prefix_end >= LEFT(child.code_prefix_end, char_length(parent.code_prefix_end))
                   AND parent.id != child.id
                   AND parent.company_id = child.company_id
                 WHERE child.company_id IN %(company_ids)s
            )
            UPDATE ii_edk_lista_gkag child
               SET parent_id = relation.parent_id
              FROM relation
             WHERE child.id = relation.child_id;
        """
        self.env.cr.execute(query, {'company_ids': tuple(self.company_id.ids)})
        self.invalidate_model(['parent_id'])
        self.search([('company_id', 'in', self.company_id.ids)])._parent_store_update()

class TipoviDokumentarnogMaterijala(models.Model):
    _name = 'ii.edk.document.type'
    _description = 'Sifarnik ili vrsta dokumenata '


    name = fields.Char(string="Document Type", required=True, tracking=True)
    code = fields.Char(size=64, required=True, tracking=True)
    mandatory_signature = fields.Boolean("Mandatory Signature")
    mandatory_approval = fields.Boolean("Mandatory Approve Process")
    vrsta = fields.Selection(
        string='Document Group Type',
        selection=DocumentGroupType.list,
        required=True,
        default=DocumentGroupType.default,
    )


class DocumentCategoryRoot(models.Model):
    _name = 'document.category.root'
    _description = 'document codes first 2 digits'
    _auto = False

    name = fields.Char()
    parent_id = fields.Many2one('document.category.root')
    company_id = fields.Many2one('res.company')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT DISTINCT ASCII(code) * 1000 + ASCII(SUBSTRING(code,2,1)) AS id,
                   LEFT(code,2) AS name,
                   ASCII(code) AS parent_id,
                   company_id
            FROM ii_edk_lista_kag WHERE code IS NOT NULL
            UNION ALL
            SELECT DISTINCT ASCII(code) AS id,
                   LEFT(code,1) AS name,
                   NULL::int AS parent_id,
                   company_id
            FROM ii_edk_lista_kag WHERE code IS NOT NULL
            )''' % (self._table,)
        )