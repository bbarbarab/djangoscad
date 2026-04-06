from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Ente(models.Model):
    nome = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Ente"
        verbose_name_plural = "Enti"

    def __str__(self):
        return self.nome
    
class Soggetto(models.Model):
    nome = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Soggetto"
        verbose_name_plural = "Soggetti"

    def __str__(self):
        return self.nome


class TipoScadenza(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Tipo scadenza"
        verbose_name_plural = "Tipi scadenze"

    def __str__(self):
        return self.nome


class Progetto(models.Model):
    class Ricorrenza(models.TextChoices):
        ANNUALE = "annuale", "Annuale"
        UNA_TANTUM = "una_tantum", "Una tantum"

    nome = models.CharField(max_length=200, unique=True)
    soggetto = models.ForeignKey(
        Soggetto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scadenze"
    )

    ricorrenza = models.CharField(
        max_length=20,
        choices=Ricorrenza.choices,
        default=Ricorrenza.ANNUALE,
    )
    descrizione = models.TextField(blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Progetto"
        verbose_name_plural = "Progetti"

    def __str__(self):
        return self.nome


class EdizioneProgetto(models.Model):
    progetto = models.ForeignKey(
        Progetto,
        on_delete=models.CASCADE,
        related_name="edizioni"
    )
    anno = models.PositiveIntegerField(null=True, blank=True)
    titolo = models.CharField(max_length=255, blank=True)
    una_tantum = models.BooleanField(default=False)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["progetto__nome", "anno"]
        verbose_name = "Edizione progetto"
        verbose_name_plural = "Edizioni progetto"
        constraints = [
            models.UniqueConstraint(
                fields=["progetto", "anno"],
                name="unique_progetto_anno"
            )
        ]

    def __str__(self):
        if self.una_tantum:
            return self.titolo or f"{self.progetto.nome} (una tantum)"
        if self.anno:
            return f"{self.progetto.nome} {self.anno}"
        return self.titolo or self.progetto.nome

class Scadenza(models.Model):

    class Stato(models.TextChoices):
        DA_FARE = "da_fare", "Da fare"
        IN_CORSO = "in_corso", "In corso"
        FATTO = "fatto", "Fatto"
        IN_ATTESA = "in_attesa", "In attesa"
        DA_CHIARIRE = "da_chiarire", "Da chiarire"

    class Priorita(models.TextChoices):
        ALTA = "alta", "Alta"
        MEDIA = "media", "Media"
        BASSA = "bassa", "Bassa"

    edizione = models.ForeignKey(
        EdizioneProgetto,
        on_delete=models.CASCADE,
        related_name="scadenze"
    )

    ente = models.ForeignKey(
        Ente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scadenze"
    )
    tipo = models.ForeignKey(
        TipoScadenza,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scadenze"
    )

    titolo = models.CharField(max_length=255)
    descrizione = models.TextField(blank=True)

    responsabili = models.ManyToManyField(
        User,
        blank=True,
        related_name="scadenze_assegnate"
    )

    stato = models.CharField(
        max_length=20,
        choices=Stato.choices,
        default=Stato.DA_FARE
    )
    priorita = models.CharField(
        max_length=10,
        choices=Priorita.choices,
        default=Priorita.MEDIA
    )

    data_avvio = models.DateField(null=True, blank=True)
    data_scadenza = models.DateField(null=True, blank=True)
    data_conclusione = models.DateField(null=True, blank=True)

    importo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["data_scadenza", "titolo"]
        verbose_name = "Scadenza"
        verbose_name_plural = "Scadenze"

    def __str__(self):
        if self.titolo:
            return self.titolo

        parti = []

        if self.tipo:
            parti.append(str(self.tipo))

        if self.ente:
            parti.append(str(self.ente))

        if self.edizione:
            parti.append(str(self.edizione))

        return " - ".join(parti) if parti else f"Scadenza {self.pk}"

    @property
    def giorni_alla_conclusione(self):
        if not self.data_conclusione:
            return None
        return (self.data_conclusione - timezone.localdate()).days

    @property
    def giorni_alla_scadenza(self):
        if not self.data_scadenza:
            return None
        return (self.data_scadenza - timezone.localdate()).days

    @property
    def in_ritardo(self):
        if not self.data_scadenza or self.stato == self.Stato.FATTO:
            return False
        return self.data_scadenza < timezone.localdate()