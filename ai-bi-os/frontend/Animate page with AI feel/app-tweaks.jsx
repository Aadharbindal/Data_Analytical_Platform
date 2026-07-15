const { useTweaks, TweaksPanel, TweakSection, TweakToggle } = window;

function AppTweaks() {
  const [t, setTweak] = useTweaks(window.TWEAK_DEFAULTS);
  return (
    <TweaksPanel>
      <TweakSection label="Playback" />
      <TweakToggle label="Motion editor" value={t.motionEditor} onChange={(v) => setTweak('motionEditor', v)} />
    </TweaksPanel>
  );
}
window.AppTweaks = AppTweaks;
