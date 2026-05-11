from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from core.models import Scadenza


class Command(BaseCommand):
    help = "Invia il riepilogo settimanale delle scadenze agli utenti."

    def handle(self, *args, **options):
        today = timezone.localdate()

        
        if today.weekday() != 6:  # 0 = lunedì
            self.stdout.write("Oggi non è lunedì: nessuna mail inviata.")
            return
            

        next_7_days = today + timedelta(days=7)

        User = get_user_model()
        users = User.objects.filter(is_active=True)

        for user in users:

            if not user.email:
                self.stdout.write(
                    self.style.WARNING(f"{user.username} senza email")
                )
                continue
            scadenze = (
                Scadenza.objects
                .filter(responsabili=user)
                .exclude(stato=Scadenza.Stato.FATTO)
                .filter(data_scadenza__isnull=False)
                .order_by("data_scadenza")
            )

            scadute = scadenze.filter(data_scadenza__lt=today)
            prossime = scadenze.filter(
                data_scadenza__gte=today,
                data_scadenza__lte=next_7_days,
            )
            altre = scadenze.filter(data_scadenza__gt=next_7_days)[:10]

            tutte_aperte = (
                Scadenza.objects
                .exclude(stato=Scadenza.Stato.FATTO)
                .filter(data_scadenza__isnull=False)
                .order_by("data_scadenza")[:15]
            )

            if (
                not scadute.exists()
                and not prossime.exists()
                and not altre.exists()
                and not tutte_aperte.exists()
            ):
                continue

            nome = user.first_name or user.username

            try:
                avatar = user.profilo.emoji()
            except Exception:
                avatar = "👋"

            righe = [
                f"{avatar} Ciao {nome},",
                "",
                "ecco il riepilogo settimanale delle *tue* scadenze.",
                "",
            ]

            if scadute.exists():
                righe.append("SCADUTE")
                for s in scadute:
                    righe.append(
                        f"- {s.edizione} — {s.tipo or '—'} — {s.ente or '—'} "
                        f"(scadenza: {s.data_scadenza.strftime('%d/%m/%Y')})"
                    )
                righe.append("")

            if prossime.exists():
                righe.append("*ENTRO 7 GIORNI*")
                for s in prossime:
                    giorni = s.giorni_alla_scadenza
                    quando = "oggi" if giorni == 0 else f"tra {giorni} gg"
                    righe.append(
                        f"- {s.edizione} — {s.tipo or '—'} — {s.ente or '—'} "
                        f"({quando}, {s.data_scadenza.strftime('%d/%m/%Y')})"
                    )
                righe.append("")

            if altre.exists():
                righe.append("*SCADENZE APERTE*")
                for s in altre:
                    righe.append(
                        f"- {s.edizione} — {s.tipo or '—'} — {s.ente or '—'} "
                        f"(scadenza: {s.data_scadenza.strftime('%d/%m/%Y')})"
                    )
                righe.append("")

            if tutte_aperte.exists():
                righe.append("")
                righe.append("=== RIEPILOGO GENERALE ===")
                righe.append("")
                for s in tutte_aperte:
                    responsabili = ", ".join(
                        [
                            (r.get_full_name() or r.username)
                            for r in s.responsabili.all()
                        ]
                    ) or "nessun responsabile"

                    righe.append(
                        f"- {s.edizione} — {s.tipo or '—'} — {s.ente or '—'} "
                        f"({s.get_stato_display()}, scadenza: {s.data_scadenza.strftime('%d/%m/%Y')}, "
                        f"resp.: {responsabili})"
                    )
                righe.append("")

            righe.append("")
            righe.append("🔗 Accedi allo scadenzario per ulteriori dettagli:")
            righe.append(settings.SCADENZARIO_URL)

            subject = "Scadenzario — riepilogo settimanale"
            body = "\n".join(righe)

            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            self.stdout.write(self.style.SUCCESS(f"Mail inviata a {user.email}"))