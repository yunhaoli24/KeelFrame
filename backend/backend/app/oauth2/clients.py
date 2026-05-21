"""OAuth2 provider clients."""

from fastapi_oauth20 import (  # pyright: ignore[reportMissingModuleSource]
    GitHubOAuth20,
    GoogleOAuth20,
    LinuxDoOAuth20,
)

from backend.core.conf import settings


github_client = GitHubOAuth20(settings.OAUTH2_GITHUB_CLIENT_ID, settings.OAUTH2_GITHUB_CLIENT_SECRET)
google_client = GoogleOAuth20(settings.OAUTH2_GOOGLE_CLIENT_ID, settings.OAUTH2_GOOGLE_CLIENT_SECRET)
linux_do_client = LinuxDoOAuth20(settings.OAUTH2_LINUX_DO_CLIENT_ID, settings.OAUTH2_LINUX_DO_CLIENT_SECRET)
