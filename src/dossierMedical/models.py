from django.db import models
from admin_app.models import User

# Create your models here.
class Patient(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    age = models.PositiveIntegerField()
    adresse = models.CharField(max_length=255)
    telephone = models.CharField(max_length=15)
    medecin = models.ForeignKey(User, on_delete=models.CASCADE)


class Visite(models.Model):
    dateRdv = models.DateTimeField(verbose_name="Date et heure du prochain bilan")
    motif = models.TextField(blank=True, null=True, default="")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visites')
    
    def __str__(self):
        return f"{self.dateRdv}"
    
    
class DossierMedical(models.Model):
    TYPE_HISTO_CHOICES = [
        ("Papillaire", "Papillaire"),
        ("Vesiculaire", "Vesiculaire"),
        ("PapilloVesiculaire", "PapilloVesiculaire"),
        ("Medullaire", "Medullaire"),
        ("Anaplasique", "Anaplasique"),
        ("Autres", "Autres"),
    ]
    
    CLAST_CHOICES = [
        ("Tx", "Tx"),
        ("T0", "T0"),
        ("T1a", "T1a"),
        ("T1b", "T1b"),
        ("T2", "T2"),
        ("T3a", "T3a"),
        ("T3b", "T3b"),
        ("T4a", "T4a"),
        ("T4b", "T4b"),
    ]
    
    CLASN_CHOICES = [
        ("Nx", "Nx"),
        ("N0", "N0"),
        ("N1a", "N1a"),
        ("N1b", "N1b"),
    ]
    
    CLASM_CHOICES = [
        ("Mx", "Mx"),
        ("M0", "M0"),
        ("M1", "M1"),
    ]
    
    MULTIFOC_CHOICES = [
        ("Uni", "Unifocale"),
        ("Bi", "Bifocale"),
        ("Multi", "Multifocale"),
    ]
    
    STADE_CHOICES = [
        ("I", "Stade I"),
        ("II", "Stade II"),
        ("III", "Stade III"),
        ("IVA", "Stade IVA"),
        ("IVB", "Stade IVB"),
    ]
    
    RISQUE_CHOICES = [
        ("Faible", "Faible"),
        ("Intermediaire", "Intermédiaire"),
        ("Haut", "Haut"),
    ]
    
    METASTASE_CHOICES = [
        ("Ganglionaire", "Ganglionaire"),
        ("Pulmonaire", "Pulmonaire"),
        ("Oseuse", "Oseuse"),
        ("Hépatique", "Hépatique"),
        ("Cerebrale", "Cérébrale"),
        ("Autres", "Autres"),
    ]
    
    CURAGE_CHOICES = [
        ("1temps", "1 Temps"),
        ("2temps", "2 Temps"),
        ("curage", "Curage"),
    ]
    
    CIRCONSTANCES_CHOICES = [
        ("Nodule", "Nodule"),
        ("DecouverteFortuite", "Découverte Fortuite"),
        ("gnm", "GNM"),
        ("adp", "ADP"),
        ("Metastase", "Métastase"),
        ("Autres", "Autres"),
    ]

    numDossier = models.CharField(max_length=50, unique=True)
    antecedentPersonnel = models.TextField(blank=True, null=True)
    carcinomeFamiliale = models.BooleanField(default=False)
    antecedentFamiliaux = models.TextField(blank=True, null=True)
    ageDecouverte = models.PositiveIntegerField(blank=True, null=True)
    effraCapsulaire = models.BooleanField(default=False)
    embonVasculaire = models.BooleanField(default=False)
    nbrCure = models.IntegerField(null=True, default=0)
    activiteCumule = models.IntegerField(null=True, default=0)
    thera = models.TextField(max_length=255, null=True, default="")
    
    # Champs de sélection simple
    typeHisto = models.CharField(max_length=255, choices=TYPE_HISTO_CHOICES, blank=True, null=True)
    clasT = models.CharField(max_length=50, choices=CLAST_CHOICES, blank=True, null=True)
    clasN = models.CharField(max_length=50, choices=CLASN_CHOICES, blank=True, null=True)
    clasM = models.CharField(max_length=50, choices=CLASM_CHOICES, blank=True, null=True)
    focalite = models.CharField(max_length=50, choices=MULTIFOC_CHOICES, blank=True, null=True)
    stade = models.CharField(max_length=50, choices=STADE_CHOICES, blank=True, null=True)
    risque = models.CharField(max_length=50, choices=RISQUE_CHOICES, blank=True, null=True)

    # Champs de sélection multiple
    metastase = models.JSONField(blank=True, null=True, help_text="Liste des métastases (sélection multiple)")
    curage = models.JSONField(blank=True, null=True, help_text="Liste des curages (sélection multiple)")
    circonstance = models.JSONField(blank=True, null=True, help_text="Liste des circonstances de découverte (sélection multiple)")

    # Champs des cures
    cure1 = models.TextField(blank=True, null=True, default="")
    cure2 = models.TextField(blank=True, null=True, default="")
    cure3 = models.TextField(blank=True, null=True, default="")
    cure4 = models.TextField(blank=True, null=True, default="")
    cure5 = models.TextField(blank=True, null=True, default="")
    cure6 = models.TextField(blank=True, null=True, default="")
    cure7 = models.TextField(blank=True, null=True, default="")
    cure8 = models.TextField(blank=True, null=True, default="")
    cure9 = models.TextField(blank=True, null=True, default="")
    cure10 = models.TextField(blank=True, null=True, default="")
    
    # Champs des bilans
    bilan1 = models.TextField(blank=True, null=True, default="")
    bilan2 = models.TextField(blank=True, null=True, default="")
    bilan3 = models.TextField(blank=True, null=True, default="")
    bilan4 = models.TextField(blank=True, null=True, default="")
    bilan5 = models.TextField(blank=True, null=True, default="")
    bilan6 = models.TextField(blank=True, null=True, default="")
    bilan7 = models.TextField(blank=True, null=True, default="")
    bilan8 = models.TextField(blank=True, null=True, default="")
    bilan9 = models.TextField(blank=True, null=True, default="")
    bilan10 = models.TextField(blank=True, null=True, default="")
    
    # Champs des examens
    examen1 = models.TextField(blank=True, null=True, default="")
    examen2 = models.TextField(blank=True, null=True, default="")
    examen3 = models.TextField(blank=True, null=True, default="")
    examen4 = models.TextField(blank=True, null=True, default="")
    examen5 = models.TextField(blank=True, null=True, default="")
    examen6 = models.TextField(blank=True, null=True, default="")
    examen7 = models.TextField(blank=True, null=True, default="")
    examen8 = models.TextField(blank=True, null=True, default="")
    examen9 = models.TextField(blank=True, null=True, default="")
    examen10 = models.TextField(blank=True, null=True, default="")
    
    # Champs des defrenations
    defrenations1 = models.TextField(blank=True, null=True, default="")
    defrenations2 = models.TextField(blank=True, null=True, default="")
    defrenations3 = models.TextField(blank=True, null=True, default="")
    defrenations4 = models.TextField(blank=True, null=True, default="")
    defrenations5 = models.TextField(blank=True, null=True, default="")

    # Autres informations
    resume = models.TextField(blank=True, null=True)
    consigne = models.TextField(blank=True, null=True)
    refrac = models.TextField(blank=True, null=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"{self.numDossier}"