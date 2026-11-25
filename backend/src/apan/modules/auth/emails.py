"""E-mail templates (pt-BR: the only user-facing text the backend produces)."""

from apan.core.mail import Mail


def _reset_link(frontend_url: str, token: str) -> str:
    # Fragment, not query string: the token never reaches server logs or Referer.
    return f"{frontend_url.rstrip('/')}/reset-password#token={token}"


def password_reset(
    to: str, full_name: str, frontend_url: str, token: str, ttl_minutes: int
) -> Mail:
    return Mail(
        to=to,
        subject="APAN Frequência — redefinição de senha",
        body=(
            f"Olá, {full_name}.\n\n"
            "Recebemos um pedido para redefinir a sua senha no APAN Frequência.\n"
            "Para criar uma nova senha, acesse o link abaixo "
            f"(válido por {ttl_minutes} minutos):\n\n"
            f"{_reset_link(frontend_url, token)}\n\n"
            "Se você não fez esse pedido, ignore este e-mail: a sua senha continua a mesma.\n"
        ),
    )


def invite(to: str, full_name: str, frontend_url: str, token: str, ttl_hours: int) -> Mail:
    return Mail(
        to=to,
        subject="APAN Frequência — convite de acesso",
        body=(
            f"Olá, {full_name}.\n\n"
            "Uma conta foi criada para você no APAN Frequência.\n"
            f"Para definir a sua senha, acesse o link abaixo (válido por {ttl_hours} horas):\n\n"
            f"{_reset_link(frontend_url, token)}\n\n"
            "Se você não esperava este convite, ignore este e-mail.\n"
        ),
    )
