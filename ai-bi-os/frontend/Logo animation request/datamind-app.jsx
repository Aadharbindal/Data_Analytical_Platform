// datamind-app.jsx — wires tweaks + SceneStage together for the DataMind logo animation
(function () {
  const { React, useTweaks, TweaksPanel, TweakSection, TweakToggle, TweakColor,
          SceneStage, DataMindScene, DataMindConfigContext } = window;

  function App() {
    const [t, setTweak] = useTweaks(window.DATAMIND_TWEAK_DEFAULTS);

    const cfg = React.useMemo(() => ({
      accent: t.accent,
      showGrid: t.showGrid,
      showOrbit: t.showOrbit,
    }), [t.accent, t.showGrid, t.showOrbit]);

    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        <DataMindConfigContext.Provider value={cfg}>
          <SceneStage width={1280} height={720} scenes={window.OM_SCENES} playback={window.OM_PLAYBACK} bg="#05070c">
            {{ Reveal: DataMindScene }}
          </SceneStage>
        </DataMindConfigContext.Provider>

        <TweaksPanel>
          <TweakToggle label="Motion editor" value={t.motionEditor} onChange={(v) => setTweak('motionEditor', v)} />
          <TweakSection label="Look" />
          <TweakColor label="Accent color" value={t.accent}
                      options={['#3b82f6', '#22c55e', '#a855f7', '#f59e0b']}
                      onChange={(v) => setTweak('accent', v)} />
          <TweakToggle label="Dashboard grid" value={t.showGrid} onChange={(v) => setTweak('showGrid', v)} />
          <TweakToggle label="Orbit dot" value={t.showOrbit} onChange={(v) => setTweak('showOrbit', v)} />
        </TweaksPanel>
      </div>
    );
  }

  window.App = App;
})();
