import { DiscordSDK } from '@discord/embedded-app-sdk';

const DEFAULT_DISCORD_CLIENT_ID = '1514005235205668924';

export function isDiscordActivityLaunch() {
  const params = new URLSearchParams(window.location.search);
  return params.has('frame_id') || params.has('instance_id') || params.has('platform') || window.location.hostname.endsWith('discordsays.com');
}

export async function connectDiscordActivity() {
  const clientId = (import.meta.env.VITE_DISCORD_CLIENT_ID || DEFAULT_DISCORD_CLIENT_ID).trim();
  if (!clientId || !isDiscordActivityLaunch()) {
    return { active: false, ready: false, clientId };
  }
  const sdk = new DiscordSDK(clientId);
  await sdk.ready();
  return {
    active: true,
    ready: true,
    clientId,
    sdk,
    context: sdk.instanceId ? { instanceId: sdk.instanceId } : null,
  };
}
