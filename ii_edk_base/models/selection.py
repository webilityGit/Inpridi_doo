# -*- coding: utf-8 -*-

class Selection(object):
    list = []
    folded = []
    default = None

    @classmethod
    def name(cls, state):
        states_dict = dict(cls.list)
        if state in states_dict:
            return states_dict[state]

    @classmethod
    def values(cls):
        return list(dict(cls.list))


class ApproverState(Selection):

    list = [
        ('to approve', 'To Approve'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),

    ]
    default = list[0][0]
 # status dokumenta u odnosu na arhivu, i to: potpisan odnosno pečatiran, potpisan i pečatiran, nadograđen/obnovljen, uništen, predat javnom arhivu;



class ApprovalMethods(Selection):
    list = [
        ('button', 'Button'),
    ]
    default = list[0][0]


class DocumentState(Selection):
    list = [
        ('draft', 'Draft'),
        ('approval', 'Approval'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('posted', 'Posted'),
    ]
    default = list[0][0]
class DocumentArchiveState(Selection):
    list = [
        ('draft', 'In preparation'),
        ('sORs', 'Signed or Siled'),
        ('sANDs', 'Signed and Siled'),
        ('rewoked', 'Rewoked'),
        ('distroed', 'Distroed'),
        ('submitted', 'Submitted to the archives'),

    ]
    default = list[0][0]

class CaseState(Selection):
    list = [
        ('draft', 'Draft'),
        ('inprocess', 'In Process'),
        ('onhold', 'On Hold'),
        ('cancelled', 'Canceled'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
        ('arhived', 'Arhived'),
    ]
    default = list[0][0]



# Lubi TODO dodati u modulu ii_edk_project
# class Doclass DocumentType(Selection):
#    list = [
#        ('invoice_in', 'Faktura Dobavljača'),
#        ('invoice_out', 'Faktura Kupca'),
#        ('invoice_advanced', 'Avansna faktura'),
#        ('refund_in', 'Knjizno zaduženje'),
#        ('refund_out', 'Knjižno odobrenje'),
#        ('fiscal', 'Trošak - fiskalni račun'),
#        ('contract', 'Ugovor'),
#        ('statement', 'Izvod banke'),
#        ('project', 'Projektna dokumentacija'),
#        ('other_doc', 'Ostalo'),
#   ]
#    default = list[0][0]cumentProjectType(Selection):
#     list = [
#         ('1', 'Naši dopisi'),
#         ('2', 'Dopisi drugih'),
#         ('5', 'Ugovori'),
#         ('6', 'Ponude'),
#         ('7', 'Revers'),
#         ('8', 'Rešenja'),
#         ('9', 'Zapisnik o primopredaji'),
#         ('10', 'Obaveštenja'),
#         ('11', 'Tenderska dokumentacija'),
#         ('12', 'Izveštaji'),
#     ]
#     default = list[0][0]
# class DocumentProjectGroup(Selection):
#     list = [
#         ('1', 'IT industrija'),
#         ('2', 'Arhitektura/Gradjevina'),
#         ('3', 'Saobracaj'),
#         ('4', 'Kultura'),
#         ('5', 'NGO'),
#         ('6', 'Standardizacija'),
#         ('7', 'Ekologija'),
#         ('8', 'Proizvodnja'),
#         ('9', 'Servis'),
#         ('10', 'Ostalo'),
#     ]
#     default = list[0][0]


class DocumentVisibility(Selection):
    list = [
        ('all_users', 'All Users'),
        ('followers', 'Followers'),
        ('approvers', 'Approvers'),
    ]
    default = list[0][0]

class DocumentGroupType(Selection):
    list = [
        ('fin', 'Finansijski dokumenat'),
        ('low', 'Pravni dokumenti'),
        ('others', 'Ostala dokumenta'),
    ]
    default = list[0][0]

class DocumentMove(Selection):
    list = [
        ('in', 'Incoming'),
        ('out', 'Outgoing'),
        ('int', 'Internal'),
    ]
    default = list[0][0]
class IzvorniOblik(Selection):
    list = [
        ('paper', 'Paper'),
        ('digital', 'Digital'),

    ]
    default = list[0][0]
class SaveFormat(Selection):
    list = [
        ('paper', 'Paper'),
        ('pdf', 'PDF'),
        ('xml', 'XML'),
    ]
    default = list[0][0]


class ApprovalStep(Selection):
    step_range = list(range(1, 21))
    list = [("{:02d}".format(step), "{:02d}".format(step)) for step in step_range]
    default = list[0][0]


### Dodatak za efakture
# Lubi TODO dodati u modulu ii_edk_sef
class DocumentSource(Selection):
    list = [
        ('manual', 'Manual'),
        ('sef', 'SEF'),
        ('email', 'Email'),
    ]
    default = list[0][0]
#
#
# class DocumentSefStatus(Selection):
#     list = [
#         ('New', 'Novo'),
#         ('Seen', 'Pregledano'),
#         ('Reminded', 'Podsetnik poslat'),
#         ('Renotified ', 'Ponovo obavesteni'),
#         ('Cancelled', 'Otkazano'),
#         ('Storno', 'Stornirano'),
#         ('Approved', 'Odobreno'),
#         ('Rejected', 'Odbijeno'),
#         ('Deleted', 'Obrisano'),
#     ]
#     default = list[0][0]
