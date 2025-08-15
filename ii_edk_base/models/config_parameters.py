# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
from .selection import (ApprovalMethods, DocumentState, ApproverState, ApprovalStep,
                DocumentVisibility, DocumentSource, CaseState, DocumentArchiveState)

class eDKconfig(models.Model):
    _name = 'ii.edk.config'
    _description = 'Config Parameters for electronic workbook of received and sent documents '

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Name', required=True,)

    visibility = fields.Selection(
        string='Visibility',
        selection=DocumentVisibility.list,
        required=True,
        default=DocumentVisibility.default,
    )
    workbook_main_user_id = fields.Many2one( string='workbook officer', comodel_name='res.users', required=True, default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True,

    )
    approval_participant_id = fields.Many2one(
        string='Approval Team',
        comodel_name='ii.edk.participants',
        required=True,


        #     domain="[('company_id', '=', company_id)]",   Lubi Morao da zakomentarisem jer nece da prodje upgrade
    )
    docType = fields.Many2one(
        string ='Tip Dokumenta',
        comodel_name = 'ii.edk.document.type',
        help = "Ovo polje se koristi za automatsko razvrstavanje dokumenata sa SEF-a",
    )
    classificationID_U = fields.Many2one(
        string ='Klasifikacija ulaznih finansijskih dokumenta',
        comodel_name = 'ii.edk.lista.kag',
        help = "Ovo polje se koristi za automatsku klasifikaciju ulazne finansijske dokumentacije sa SEF-a",
    )
    classificationID_I = fields.Many2one(
        string='Klasifikacija izlaznih finansijskih dokumenta',
        comodel_name='ii.edk.lista.kag',
        help="Ovo polje se koristi za automatsku klasifikaciju izlazne finansijske dokumentacije sa SEF-a",
    )

    # Validation

#    @api.constrains('company_id')
 #   def _check_team_company(self):
 #       for team in self:
 #           team.approval_participant_id.validate_company(team.company_id)

###   Dodao lubi novu abstractnu klasu

    def validate_company(self, company):
        if not company:
            return
        for approver in self:
            if company not in approver.user_id.company_ids:
                raise ValidationError(
                    _('%s does not have access to the company %s') % (approver.user_id.name, company.name))
# Lubi TODO prebaciti u modul ii_edk_project
# class DocProjectTypes(models.Model):
#     _name = 'xf.doc.project.types'
#     _description = 'Doc Project Types Config tabele'
#
#     active = fields.Boolean('Active', default=True)
#
#     name = fields.Char(
#         string='Name',
#         required=True,
#     )
#     code = fields.Char(
#             string='Code',
#             required=True,
#     )
#
#     project_doc_group = fields.Selection(
#         string='Project Documentation Group',
#         selection=DocumentProjectGroup.list,
#         required=True,
#         default=DocumentProjectGroup.default,
#     )

# class KategorijeArhivskeGradje(models.Model):
#     _name = 'ii.edk.lista.kag'
#     _description = 'Lista kategorija arhivske građe i dokumentarnog materijala'
#
#     active = fields.Boolean('Active', default=True)
#     redni_broj = fields.Char(
#         string='Seq. Number',
#         required=True,
#     )
#
#     name = fields.Char(
#         string='Category Name ', # Naziv kategorije dokumentarnog materijala'
#         required=True,
#     )
#
#     naziv_grupe = fields.Many2one(
#         string='Categiry Group Name',    #Naziv grupe KDM'
#         comodel_name='ii.edk.lista.gkag',
#         required=True,
#     )
#     klasifikaciona_oznaka = fields.Char(
#         string='Classification tag',
#     )
#     rok_cuvanja_meseci = fields.Integer(
#         string='Storage Period in mounths',
#         required=True,
#     )
#     napomena = fields.Char(
#         string='Note related to storage period',)
#
#     rok_cuvanja_godina = fields.Char(
#         string='Storage Period in years',
#         compute = '_compute_rok_cuvanja',
#     )
#     def _compute_rok_cuvanja(self):
#         temp_tekst = " "
#         if self.rok_cuvanja_meseci:
#             temp_tekst = char(self.rok_cuvanja_meseci / 12) + " godina "
#
#             if self.napomena:
#                 temp_tekst = elf.rok_cuvanja_godina + self.napomena
#         return temp_tekst
#
# class GrupeKategorijeArhivskeGradje(models.Model):
#     _name = 'ii.edk.lista.gkag'
#     _description = 'Lista Grupa kategorija arhivske građe i dokumentarnog materijala'
#
#     active = fields.Boolean('Active', default=True)
#
#     name = fields.Char(
#         string='Group Name ', # Naziv Grupe kategorije dokumentarnog materijala'
#         required=True,
#     )
#     redni_broj = fields.Char(
#         string='Seq. Number',
#         required=True,
#     )
#
class Predmeti(models.Model):
    _name = 'ii.edk.lista.predmeta'
    _description = 'Lista predmets u kancelsrijskom poslovanju'

    active = fields.Boolean('Active', default=True)

    name = fields.Char(
        string='Case Name',
        required=True,
    )
#    predmet_broj = fields.Char(
#        string='Case Number',
#        required=True,
#    )   -->
    case_state = fields.Selection(
        string='Case status',
        selection=CaseState.list,
        required=True,
        default=CaseState.default,
        readonly=True,
        tracking=True,
    )
    case_date = fields.Date(
        string='Case date',
        required=True,
        default=datetime.now(),

        tracking=True,
    )
    case_arhive_date = fields.Date(
        string='Case Archived Date',
        readonly=True,

        tracking=True,
    )
    document_ids = fields.One2many(
        string='Documents',
        comodel_name='ii.edk.document.package',
        inverse_name='broj_predmeta',
        readonly=True,
    )



