* ============================================
* DERS Fixed Effects Analysis
* Simulated panel data: y = b*x + unit FE + time FE + e
* ============================================

clear all
set more off
set seed 42

log using "ders-analysis.log", replace text

* ============================================
* Create balanced panel data
* ============================================

local n_units = 100
local n_periods = 10
local beta = 1.5

set obs `n_units'
gen id = _n
gen unit_fe = rnormal(0, 1)

expand `n_periods'
bysort id: gen year = 2015 + _n - 1

gen x = rnormal(0, 1)
gen e = rnormal(0, 1)
gen time_fe = 0.20 * (year - 2015)
gen y = `beta' * x + unit_fe + time_fe + e

xtset id year

* ============================================
* Fixed effects regression
* ============================================

xtreg y x i.year, fe vce(cluster id)
estimates store fe_model

* Save a compact results table.
estimates table fe_model, b(%9.3f) se(%9.3f) stats(N r2_w r2_b r2_o)

log close
