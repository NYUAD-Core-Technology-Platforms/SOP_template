## Startup

1. Log into the booking system and confirm your reservation
2. Power on the microscope using the main switch (right side panel)
3. Turn on the laser key switch (key must remain in the ON position during use)
4. Wait **15 minutes** for the laser to warm up and stabilize
5. Launch the ZEN imaging software from the desktop shortcut
6. Verify the interlock indicator shows GREEN on the control panel

> **Important**: Do not proceed if the interlock indicator is RED. Report to lab supervisor immediately.

## Sample Preparation

1. Clean the objective lens with lens tissue moistened with lens cleaning solution
2. If using the 63x oil objective, apply a small drop of immersion oil (Type F) directly to the coverslip
3. Place your sample on the motorized stage — ensure the slide is seated flat
4. Use the coarse focus knob to bring the sample into approximate focus

> **Tip**: For thick samples, start with the 10x objective to find your region of interest before switching to higher magnification.

## Imaging

1. Select the appropriate laser line for your fluorophore:
   - **488 nm** — GFP, Alexa 488, FITC
   - **561 nm** — mCherry, Alexa 568, TRITC
   - **633 nm** — Alexa 647, Cy5
2. Set the pinhole to **1 Airy Unit** for confocal imaging
3. Use **Live** mode to find and frame your region of interest
4. Adjust imaging parameters:
   - **Gain**: Start at 600, increase if signal is weak
   - **Laser power**: Use minimum power needed (typically 2-10%)
   - **Offset**: Adjust so background appears just above zero
5. For single images: click **Snap**
6. For Z-stacks: set top and bottom limits, choose step size (Nyquist recommended)
7. For time-lapse: configure interval and total duration in the **Time Series** panel

> **Warning**: Keep laser power below 15% to avoid photobleaching. For live cell imaging, use minimal laser power and increase gain instead.

## Data Export

1. Save your data in .czi format (native) to your designated project folder
2. For publication, export as TIFF:
   - Go to **Processing → Export**
   - Select **TIFF** format, **16-bit** depth
   - Include scale bar if needed
3. Record your session in the instrument logbook (date, user, samples, objectives used)

## Shutdown

1. Remove your sample from the stage
2. Clean any immersion oil from the objective using lens tissue with cleaning solution
3. Set all lasers to **Standby** in the software
4. Close the ZEN software
5. Turn off the laser key switch and remove the key — return to the key cabinet
6. Power off the microscope at the main switch
7. Place the dust cover over the microscope
8. Log your usage in the booking system (mark session as complete)

## Troubleshooting

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| No image visible | Laser shutter closed | Check the shutter toggle in software |
| Dim/noisy image | Laser not warmed up | Wait full 15 minutes after startup |
| Streaks in image | Dirty objective | Clean with lens tissue and solution |
| Software crash | Memory overload | Reduce image size or bit depth |
| Stage not moving | Emergency stop engaged | Release e-stop, restart software |

## Maintenance

- **Daily**: Clean objectives after each session; log usage in booking system
- **Weekly**: Check laser power output using power meter (log in maintenance book)
- **Monthly**: Clean stage area and check immersion oil supply
- **Service contract**: Zeiss Service — Contract #ZSC-2025-4421, expires 2026-12-31
- **Service records**: Located in lab filing cabinet, drawer 2, and on shared drive /maintenance/
- **Contact for repairs**: Zeiss Service Hotline +971-4-XXX-XXXX
