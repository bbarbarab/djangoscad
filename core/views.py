from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Scadenza, Soggetto

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        today = timezone.localdate()
        last_30_days = today - timedelta(days=30)
        next_7_days = today + timedelta(days=7)

        soggetto_id = self.request.GET.get("soggetto", "").strip()

        qs = Scadenza.objects.select_related(
            "edizione",
            "edizione__progetto",
            "edizione__progetto__soggetto",
            "ente",
            "tipo",
        ).prefetch_related("responsabili")

        if soggetto_id:
            qs = qs.filter(edizione__progetto__soggetto_id=soggetto_id)

        aperte = qs.exclude(stato=Scadenza.Stato.FATTO)

        # Contatori sintetici dashboard
        ctx["in_ritardo"] = aperte.filter(
            data_scadenza__isnull=False,
            data_scadenza__lt=today,
        ).count()

        ctx["da_chiudere_presto"] = aperte.filter(
            data_scadenza__isnull=False,
            data_scadenza__gte=today,
            data_scadenza__lte=next_7_days,
        ).count()

        ctx["in_corso_count"] = qs.filter(
            stato=Scadenza.Stato.IN_CORSO
        ).count()

        ctx["ultimo_mese_count"] = aperte.filter(
            data_scadenza__isnull=False,
            data_scadenza__gte=last_30_days,
        ).count()

        # Tabella 1: cose da chiudere in 7 giorni
        ctx["da_chiudere"] = aperte.filter(
            data_scadenza__isnull=False,
            data_scadenza__lte=next_7_days,
        ).order_by("data_scadenza", "data_scadenza")[:15]

        # Tabella 2: cose da fare e in corso da concludere in 60 giorni
        next_60_days = today + timedelta(days=60)

        ctx["in_corso"] = qs.filter(
            stato=Scadenza.Stato.IN_CORSO,
        ).order_by("data_scadenza")[:10]

        ctx["da_fare"] = qs.filter(
            stato=Scadenza.Stato.DA_FARE,
            data_scadenza__isnull=False,
            data_scadenza__lte=next_60_days,
        ).order_by("data_scadenza")[:10]

        ctx["attivita_aperte"] = qs.filter(
            stato__in=[Scadenza.Stato.IN_CORSO, Scadenza.Stato.DA_FARE],
            data_scadenza__isnull=False,
            data_scadenza__lte=next_60_days,
        ).order_by("data_scadenza")[:20]

        ctx["soggetti"] = Soggetto.objects.all().order_by("nome")
        ctx["soggetto_selezionato"] = soggetto_id
        ctx["oggi"] = today
        ctx["prossimi_7"] = next_7_days

        return ctx

class ScadenzaListView(LoginRequiredMixin, ListView):
    model = Scadenza
    template_name = "core/scadenza_list.html"
    context_object_name = "scadenze"
    paginate_by = 25

    def get_queryset(self):
        qs = Scadenza.objects.select_related(
            "edizione",
            "edizione__progetto",
            "edizione__progetto__soggetto",
            "ente",
            "tipo",
        ).prefetch_related("responsabili")

        soggetto_id = self.request.GET.get("soggetto", "").strip()
        stato = self.request.GET.get("stato", "").strip()
        progetto_id = self.request.GET.get("progetto", "").strip()
        responsabile_id = self.request.GET.get("responsabile", "").strip()

        if soggetto_id:
            qs = qs.filter(edizione__progetto__soggetto_id=soggetto_id)

        if stato:
            qs = qs.filter(stato=stato)

        if progetto_id:
            qs = qs.filter(edizione__progetto_id=progetto_id)
        if responsabile_id:
            qs = qs.filter(responsabili__id=responsabile_id)

        from django.db.models import Case, When, Value, IntegerField

        qs = qs.annotate(
            ordine_stato=Case(
                When(stato=Scadenza.Stato.FATTO, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            ordine_priorita=Case(
                When(priorita=Scadenza.Priorita.ALTA, then=Value(0)),
                When(priorita=Scadenza.Priorita.MEDIA, then=Value(1)),
                When(priorita=Scadenza.Priorita.BASSA, then=Value(2)),
                output_field=IntegerField(),
            ),
        )

        return qs.order_by(
            "ordine_stato",      # prima non fatti
            "ordine_priorita",   # alta → media → bassa
            "data_scadenza"      # più vicine prima
        ).distinct()

    def get_context_data(self, **kwargs):
        
        ctx = super().get_context_data(**kwargs)
        from .models import Progetto
        
        User = get_user_model()
        
        ctx["soggetti"] = Soggetto.objects.all().order_by("nome")
        ctx["progetti"] = Progetto.objects.select_related("soggetto").order_by("nome")
        ctx["soggetto_selezionato"] = self.request.GET.get("soggetto", "").strip()
        ctx["stato_selezionato"] = self.request.GET.get("stato", "").strip()
        ctx["progetto_selezionato"] = self.request.GET.get("progetto", "").strip()
        
        ctx["responsabili"] = User.objects.filter(is_active=True).order_by("first_name", "username")
        ctx["responsabile_selezionato"] = self.request.GET.get("responsabile", "").strip()
        
        return ctx

