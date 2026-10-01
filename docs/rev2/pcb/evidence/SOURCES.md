# Manufacturer sources used by the evidence register

The evidence register (`Hardware/Rev2_Controller/calc/datasheet_inputs.json`) cites manufacturer documents by file name under
`docs/rev2/pcb/evidence/`. **Those PDFs and vendor CAD models are not redistributed in this repository** (they are the
manufacturers' copyrighted documents and several carry no-redistribution notices). Download them from the manufacturer if you
want to re-verify an entry; place them in this folder under the file names below and the verification tests will find them.

| File name cited in the register | Manufacturer / document | Where to get it |
|---|---|---|
| `TI_INA228_datasheet_SLYS021A_revA.pdf` | Texas Instruments INA228, SLYS021A (rev. May 2022) | ti.com/product/INA228 |
| `ISO7721_datasheet_SLLSEP3G.pdf` | Texas Instruments ISO7721, SLLSEP3G | ti.com (ISO7721) |
| `CP2102N_datasheet_rev1.5.pdf` | Silicon Labs CP2102N, rev. 1.5 | silabs.com (CP2102N) |
| `SRN6045TA_datasheet.pdf` | Bourns SRN6045TA power inductors | bourns.com (SRN6045TA) |
| `Bourns_1.5SMBJ_datasheet.pdf` | Bourns 1.5SMBJ TVS series | bourns.com (1.5SMBJ) |
| `Littelfuse_SMF_series_datasheet_rev2023-11-02.pdf` | Littelfuse SMF series TVS, rev. 11/02/23 | littelfuse.com (SMF series) |
| `Panasonic_ERJ_P_PA_PM_anti-surge_series_24Feb22.pdf`, `Panasonic_ERJP_AOA0000C331_29Sep23.pdf`, `Panasonic_ERJP6W_0805_NRND_RDO0000C337.pdf` | Panasonic anti-surge thick-film chip resistors ERJ P/PA/PM (AOA0000C331); ERJP6W (RDO0000C337, reference only) | industrial.panasonic.com |
| `GCT_USB4105_drawing.pdf` | GCT USB4105 customer drawing | gct.co |
| `JST_PH_ePH_catalog.pdf` | JST PH series (ePH catalog) | jst-mfg.com |
| `EB21A-XX-C_drawing_revB.pdf` | Adam Tech EB21A-XX-C drawing, rev. B | adam-tech.com |
| `Samtec_FTSH-1XX-XX-XXX-DV-XXX_recommended_PCB_layout_revH.pdf`, `Samtec_FTSH-1XX-XX-XXX-DV-XXX-XXX-X-XX_product_drawing_revFX.pdf` | Samtec FTSH-1XX-XX-XXX-DV recommended PCB layout (rev. H) and product drawing (rev. FX) | suddendocs.samtec.com/prints/ |
| `Molex_22272031_product_page.pdf`, `Molex_022272041_3D_drawing_no_dimensions.pdf`, `Molex_022272031_3D_model_ProE.stp` | Molex 22-27-2031 / 22-27-2041 (KK 254, series 6410): product pages and 3D models | molex.com/en-us/products/part-detail/22272031 |

Licences of the files in this repository: see `README.md` (software MIT, hardware CERN-OHL-S-2.0).
