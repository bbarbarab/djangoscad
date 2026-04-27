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
        next_7_days = today + timedelta(days=7)

        soggetto_id = self.request.GET.get("soggetto", "").strip()
        stato = self.request.GET.get("stato", "").strip()

        qs = Scadenza.objects.select_related(
            "edizione",
            "edizione__progetto",
            "edizione__progetto__soggetto",
            "ente",
            "tipo",
        ).prefetch_related("responsabili")

        if soggetto_id:
            qs = qs.filter(edizione__progetto__soggetto_id=soggetto_id)

        if stato:
            qs = qs.filter(stato=stato)

        aperte = qs.exclude(stato=Scadenza.Stato.FATTO)
        
        # Contatori
        ctx["totale"] = qs.count()
        ctx["completate"] = qs.filter(stato=Scadenza.Stato.FATTO).count()
        ctx["in_corso_count"] = qs.filter(stato=Scadenza.Stato.IN_CORSO).count()

        ctx["in_ritardo"] = aperte.filter(
            data_conclusione__isnull=False,
            data_conclusione__lt=today
        ).count()

        ctx["da_chiudere_presto"] = aperte.filter(
            data_conclusione__isnull=False,
            data_conclusione__gte=today,
            data_conclusione__lte=next_7_days
        ).count()

        # Tabelle
        ctx["urgenti"] = aperte.filter(
            data_conclusione__isnull=False
        ).order_by("data_conclusione", "titolo")[:10]

        ctx["in_corso"] = qs.filter(
            stato=Scadenza.Stato.IN_CORSO
        ).order_by("data_conclusione", "data_scadenza", "titolo")[:10]

        ctx["ultime_completate"] = qs.filter(
            stato=Scadenza.Stato.FATTO
        ).order_by("-updated_at")[:10]

        ctx["soggetti"] = Soggetto.objects.all().order_by("nome")
        ctx["soggetto_selezionato"] = soggetto_id
        ctx["stato_selezionato"] = stato
        ctx["oggi"] = today
        ctx["prossimi_7"] = today + timedelta(days=7)
        
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

        return qs.order_by("data_conclusione", "data_scadenza", "titolo").distinct()

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

