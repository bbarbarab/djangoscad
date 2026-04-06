from django.contrib import admin
from .models import Ente, Soggetto, TipoScadenza, Progetto, EdizioneProgetto, Scadenza

@admin.register(Ente)
class EnteAdmin(admin.ModelAdmin):
    search_fields = ["nome"]

@admin.register(Soggetto)
class SoggettoAdmin(admin.ModelAdmin):
    search_fields = ["nome"]

@admin.register(TipoScadenza)
class TipoScadenzaAdmin(admin.ModelAdmin):
    search_fields = ["nome"]

@admin.register(Progetto)
class ProgettoAdmin(admin.ModelAdmin):
    list_display = ["nome", "soggetto","ricorrenza"]
    list_filter = ["soggetto", "ricorrenza"]
    search_fields = ["nome", "descrizione"]

@admin.register(EdizioneProgetto)
class EdizioneProgettoAdmin(admin.ModelAdmin):
    list_display = ["__str__", "progetto", "anno", "una_tantum"]
    list_filter = ["una_tantum", "progetto"]
    search_fields = ["titolo", "progetto__nome"]

@admin.register(Scadenza)
class ScadenzaAdmin(admin.ModelAdmin):
    list_display = [
        "titolo",
        "edizione",
        "soggetto_progetto",
        "ente",
        "tipo",
        "stato",
        "priorita",
        "data_avvio",
        "data_scadenza",
        "data_conclusione",
        "giorni_alla_scadenza_admin",
    ]
    list_filter = [
        "stato",
        "priorita",
        "ente",
        "tipo",
        "edizione__progetto",
        "edizione__progetto__soggetto",
    ]

    search_fields = [
        "titolo",
        "descrizione",
        "note",
        "edizione__progetto__nome",
        "edizione__titolo",
    ]
    filter_horizontal = ["responsabili"]
    autocomplete_fields = ["ente", "tipo", "edizione"]
    date_hierarchy = "data_scadenza"

    def soggetto_progetto(self, obj):
        if obj.edizione and obj.edizione.progetto:
            return obj.edizione.progetto.soggetto
        return None

    soggetto_progetto.short_description = "Soggetto"

    def giorni_alla_scadenza_admin(self, obj):
        return obj.giorni_alla_scadenza

    giorni_alla_scadenza_admin.short_description = "Giorni alla scadenza"

admin.site.site_header = "Gestionale scadenzario"
admin.site.site_title = "Scadenzario"
admin.site.index_title = "Amministrazione"