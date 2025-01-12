import sciris as sc
import covasim as cv
import covasim.base as cvb
import pylab as pl
import numpy as np
import matplotlib as mplt
import utils

########################################################################
# Settings and initialisation
########################################################################
# Check version
cv.check_version('3.0.0')
cv.git_info('covasim_version.json')



# Saving and plotting settings
do_plot = 1
do_save = 1
save_sim = 1
plot_hist = 0 # Whether to plot an age histogram
do_show = 0
verbose = 1
seed    = 1
n_runs = 200
to_plot = sc.objdict({
    'Cumulative tests': ['cum_tests'],
    'First vaccine dose': ['n_dose_1'],
    'Second vaccine dose': ['n_dose_2'],
    'Cumulative diagnoses': ['cum_diagnoses'],
    'Cumulative hospitalisations': ['cum_severe'],
    'Cumulative deaths': ['cum_deaths'],
    'New infections': ['new_infections'],
    'R': ['r_eff'],
})

# Define what to run
runoptions = ['quickfit', # Does a quick preliminary calibration. Quick to run, ~30s
              'scens', # Runs the 3 scenarios
              'devel']
whattorun = runoptions[0] #Select which of the above to run

# Filepaths
data_path = 'UK_Covid_cases_april27_England.xlsx'
resfolder = 'results_delay'

# Important dates
start_day = '2020-01-21'
end_day = '2021-12-31'
data_end = '2021-04-10' # Final date for calibration


########################################################################
# Create the baseline simulation
########################################################################

def make_sim(seed, beta, calibration=True, scenario=None, delta_beta=1.6, future_symp_test=None, end_day=None, verbose=0):

    # Set the parameters
    #total_pop    = 67.86e6 # UK population size
    total_pop    = 55.98e6 # UK population size
    pop_size     = 100e3 # Actual simulated population
    pop_scale    = int(total_pop/pop_size)
    pop_type     = 'hybrid'
    pop_infected = 1000
    beta         = beta
    asymp_factor = 2
    contacts     = {'h':3.0, 's':20, 'w':20, 'c':20}
    beta_layer   = {'h':3.0, 's':1.0, 'w':0.6, 'c':0.3}
    if end_day is None: end_day = '2021-04-10'

    pars = sc.objdict(
        pop_size     = pop_size,
        pop_infected = pop_infected,
        pop_scale    = pop_scale,
        pop_type     = pop_type,
        start_day    = start_day,
        end_day      = end_day,
        beta         = beta,
        asymp_factor = asymp_factor,
        contacts     = contacts,
        rescale      = True,
        rand_seed    = seed,
        verbose      = verbose,
        rel_severe_prob = 0.5,
        rel_crit_prob = 2.3,
        rel_death_prob=1.15,
    )

    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1.0 # ages 20-30
    sim['prognoses']['sus_ORs'][1] = 1.0 # ages 20-30

   # ADD BETA INTERVENTIONS
    sbv = 0.63
    beta_past  = sc.odict({'2020-02-14': [1.00, 1.00, 0.90, 0.90],
                           '2020-03-16': [1.00, 0.90, 0.80, 0.80],
                           '2020-03-23': [1.29, 0.02, 0.20, 0.20],
                           '2020-06-01': [1.00, 0.23, 0.40, 0.40],
                           '2020-06-15': [1.00, 0.38, 0.50, 0.50],
                           '2020-07-22': [1.29, 0.00, 0.30, 0.50],
                           '2020-09-02': [1.25, sbv,  0.50, 0.70],
                           '2020-10-01': [1.25, sbv, 0.50, 0.70],
                           '2020-10-16': [1.25, sbv, 0.50, 0.70],
                           '2020-10-26': [1.00, 0.00, 0.50, 0.70],
                           '2020-11-05': [1.25, sbv, 0.30, 0.40],
                           '2020-11-14': [1.25, sbv, 0.30, 0.40],
                           '2020-11-21': [1.25, sbv, 0.30, 0.40],
                           '2020-11-30': [1.25, sbv, 0.30, 0.40],
                           '2020-12-03': [1.50, sbv, 0.50, 0.70],
                           '2020-12-20': [1.25, 0.00, 0.50, 0.70],
                           '2020-12-25': [1.50, 0.00, 0.20, 0.90],
                           '2020-12-26': [1.50, 0.00, 0.20, 0.90],
                           '2020-12-31': [1.50, 0.00, 0.20, 0.90],
                           '2021-01-01': [1.50, 0.00, 0.20, 0.90],
                           '2021-01-04': [1.25, 0.14, 0.30, 0.40],
                           '2021-01-11': [1.25, 0.14, 0.30, 0.40],
                           '2021-01-18': [1.25, 0.14, 0.30, 0.40],
                           '2021-01-18': [1.25, 0.14, 0.30, 0.40],
                           '2021-01-30': [1.25, 0.14, 0.30, 0.40],
                           '2021-02-08': [1.25, 0.14, 0.30, 0.40],
                           '2021-02-15': [1.25, 0.14, 0.30, 0.40],
                           '2021-02-22': [1.25, 0.14, 0.30, 0.40],
                           '2021-03-08': [1.25, sbv, 0.30, 0.50],
                           '2021-03-15': [1.25, sbv, 0.30, 0.50],
                           '2021-03-22': [1.25, sbv, 0.30, 0.50],
                           '2021-03-29': [1.25, 0.02, 0.30, 0.60],
                           '2021-04-05': [1.25, 0.02, 0.30, 0.60]
                           '2021-04-12': [1.25, 0.02, 0.40, 0.70],
                           '2021-04-19': [1.25, sbv, 0.40, 0.70],
                           '2021-04-26': [1.25, sbv, 0.40, 0.70]
                           })

    if not calibration:
        ##no schools until 8th March but assue 20% (1 in 5) in schools between 04/01-22/02; 
        ##model transmission remaining at schools as 14% (to account for 30% reduction due to school measures)
        ## reopening schools on 8th March, society stage 1 29th March, society stage 2 12th April, 
        ## society some more (stage 3) 17th May and everything (stage 4) 21st June 2021. 
        ## Projecting until end of 2021.
        if scenario == 'Roadmap_All':

            beta_scens = sc.odict({'2021-05-03': [1.25, sbv, 0.40, 0.70],
                               '2021-05-10': [1.25, sbv, 0.40, 0.70],
                               '2021-05-17': [1.25, sbv, 0.50, 0.80],
                               '2021-05-21': [1.25, sbv, 0.50, 0.80],
                               '2021-05-28': [1.25, 0.02, 0.50, 0.80],
                               '2021-06-07': [1.25, sbv, 0.50, 0.80],
                               '2021-06-21': [1.25, sbv, 0.60, 0.90],
                               '2021-06-28': [1.25, sbv, 0.60, 0.90],
                               '2021-07-05': [1.25, sbv, 0.60, 0.90],
                               '2021-07-12': [1.25, sbv, 0.60, 0.90],
                               '2021-07-19': [1.25, 0.00, 0.60, 0.90],
                               '2021-07-26': [1.25, 0.00, 0.50, 0.90],
                               '2021-08-02': [1.25, 0.00, 0.50, 0.90],
                               '2021-08-16': [1.25, 0.00, 0.50, 0.90],
                               '2021-09-01': [1.25, 0.63, 0.70, 0.90],
                               '2021-09-15': [1.25, 0.63, 0.70, 0.90],
                               '2021-09-29': [1.25, 0.63, 0.70, 0.90],
                               '2021-10-13': [1.25, 0.63, 0.70, 0.90],
                               '2021-10-27': [1.25, 0.02, 0.70, 0.90],
                               '2021-11-08': [1.25, 0.63, 0.70, 0.90],
                               '2021-11-23': [1.25, 0.63, 0.70, 0.90],
                               '2021-11-30': [1.25, 0.63, 0.70, 0.90],  
                               '2021-12-07': [1.25, 0.63, 0.70, 0.90],
                               '2021-12-21': [1.25, 0.63, 0.70, 0.90],  
                              })
            
        ## reopening schools on 8th March, society stage 1 29th March, society stage 2 12th April ONLY 
        ## NO (stage 3) 17th May and NO stage 4 21st June 2021. 
        ## Projecting until end of 2021.
        elif scenario == 'Roadmap_Stage2':

            beta_scens = sc.odict({'2021-05-03': [1.25, sbv, 0.40, 0.70],
                               '2021-05-10': [1.25, sbv, 0.40, 0.70],
                               '2021-05-17': [1.25, sbv, 0.40, 0.70],
                               '2021-05-21': [1.25, sbv, 0.40, 0.70],
                               '2021-05-28': [1.25, 0.02, 0.40, 0.70],
                               '2021-06-07': [1.25, sbv, 0.40, 0.70],
                               '2021-06-21': [1.25, sbv, 0.40, 0.70],
                               '2021-06-28': [1.25, sbv, 0.40, 0.70],
                               '2021-07-05': [1.25, sbv, 0.40, 0.70],
                               '2021-07-12': [1.25, sbv, 0.40, 0.70],
                               '2021-07-19': [1.25, 0.00, 0.40, 0.70],
                               '2021-07-26': [1.25, 0.00, 0.40, 0.70],
                               '2021-08-02': [1.25, 0.00, 0.40, 0.70],
                               '2021-08-16': [1.25, 0.00, 0.40, 0.70],
                               '2021-09-01': [1.25, 0.63, 0.70, 0.90],
                               '2021-09-15': [1.25, 0.63, 0.70, 0.90],
                               '2021-09-29': [1.25, 0.63, 0.70, 0.90],
                               '2021-10-13': [1.25, 0.63, 0.70, 0.90],
                               '2021-10-27': [1.25, 0.02, 0.70, 0.90],
                               '2021-11-08': [1.25, 0.63, 0.70, 0.90],
                               '2021-11-23': [1.25, 0.63, 0.70, 0.90],
                               '2021-11-30': [1.25, 0.63, 0.70, 0.90],  
                               '2021-12-07': [1.25, 0.63, 0.70, 0.90],
                               '2021-12-21': [1.25, 0.63, 0.70, 0.90],  
                              })
        ## reopening schools on 8th March, society stage 1 29th March, society stage 2 12th April, 
        ## and society some more (stage 3) 17th May but NO stage 4 21st June 2021. 
        ## Projecting until end of 2021.
        elif scenario == 'Roadmap_Stage3':
            beta_scens = sc.odict({'2021-05-03': [1.25, sbv, 0.40, 0.70],
                               '2021-05-10': [1.25, sbv, 0.40, 0.70],
                               '2021-05-17': [1.25, sbv, 0.50, 0.80],
                               '2021-05-21': [1.25, sbv, 0.50, 0.80],
                               '2021-05-28': [1.25, 0.02, 0.50, 0.80],
                               '2021-06-07': [1.25, sbv, 0.50, 0.80],
                               '2021-06-21': [1.25, sbv, 0.50, 0.80],
                               '2021-06-28': [1.25, sbv, 0.50, 0.80],
                               '2021-07-05': [1.25, sbv, 0.50, 0.80],
                               '2021-07-12': [1.25, sbv, 0.50, 0.80],
                               '2021-07-19': [1.25, 0.00, 0.50, 0.80],
                               '2021-07-26': [1.25, 0.00, 0.50, 0.80],
                               '2021-08-02': [1.25, 0.00, 0.50, 0.80],
                               '2021-08-16': [1.25, 0.00, 0.50, 0.80],
                               '2021-09-01': [1.25, 0.63, 0.70, 0.90],
                               '2021-09-15': [1.25, 0.63, 0.70, 0.90],
                               '2021-09-29': [1.25, 0.63, 0.70, 0.90],
                               '2021-10-13': [1.25, 0.63, 0.70, 0.90],
                               '2021-10-27': [1.25, 0.02, 0.70, 0.90],
                               '2021-11-08': [1.25, 0.63, 0.70, 0.90],
                               '2021-11-23': [1.25, 0.63, 0.70, 0.90],
                               '2021-11-30': [1.25, 0.63, 0.70, 0.90],  
                               '2021-12-07': [1.25, 0.63, 0.70, 0.90],
                               '2021-12-21': [1.25, 0.63, 0.70, 0.90],  
                              })
        beta_dict = sc.mergedicts(beta_past, beta_scens)
    else:
        beta_dict = beta_past

    beta_days = list(beta_dict.keys())
    h_beta = cv.change_beta(days=beta_days, changes=[c[0] for c in beta_dict.values()], layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=[c[1] for c in beta_dict.values()], layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=[c[2] for c in beta_dict.values()], layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=[c[3] for c in beta_dict.values()], layers='c')

    # Add a new change in beta to represent the takeover of the novel variant VOC 202012/01
    # Assume that the new variant is 60% more transmisible (https://cmmid.github.io/topics/covid19/uk-novel-variant.html,
    # Assume that between Nov 1 and Jan 30, the new variant grows from 0-100% of cases
    voc_days   = np.linspace(sim.day('2020-08-01'), sim.day('2021-02-10'), 31)
    voc_prop   = 0.51/(1+np.exp(-0.074*(voc_days-sim.day('2020-09-30')))) # Use a logistic growth function to approximate fig 2A of https://cmmid.github.io/topics/covid19/uk-novel-variant.html
    voc_change = voc_prop*1.60 + (1-voc_prop)*1.
    voc_beta = cv.change_beta(days=voc_days,
                              changes=voc_change)
    
    #additional variant in June
    #voc_days   = np.linspace(sim.day('2021-06-01'), sim.day('2021-12-10'), 31)
    #voc_prop   = 0.51/(1+np.exp(-0.074*(voc_days-sim.day('2021-07-30')))) # Use a logistic growth function to approximate fig 2A of https://cmmid.github.io/topics/covid19/uk-novel-variant.html
    #voc_change = voc_prop*1.60 + (1-voc_prop)*1.
    #voc_beta_1 = cv.change_beta(days=voc_days,
    #                          changes=voc_change)

    interventions = [h_beta, w_beta, s_beta, c_beta, voc_beta]
    #interventions = [h_beta, w_beta, s_beta, c_beta, voc_beta, voc_beta_1]

    # ADD TEST AND TRACE INTERVENTIONS
    tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
    tti_day= sim.day('2020-06-01') #intervention of tracing and enhanced testing (tti) starts on 1st June
    tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
    tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August
    tti_day_sep= sim.day('2020-09-01')
    tti_day_oct= sim.day('2020-10-01')
    tti_day_nov= sim.day('2020-11-01')
    tti_day_dec= sim.day('2020-12-01')
    tti_day_jan= sim.day('2021-01-01')
    tti_day_feb= sim.day('2021-02-01')
    tti_day_march= sim.day('2021-03-08')
    tti_day_april= sim.day('2021-03-01')
    #start of vaccinating those 75years+
    tti_day_vac1= sim.day('2021-01-03')
    #start of vaccinating 60+ old
    tti_day_vac2= sim.day('2021-01-28')
    #start of vaccinating 50+ years old
    tti_day_vac3= sim.day('2021-02-28')
    #start of vaccination 40+ years old
    tti_day_vac4= sim.day('2021-03-30')
    #start vaccinating of 30+   
    tti_day_vac5= sim.day('2021-04-28')
    #start vaccinating of 20+   
    tti_day_vac6= sim.day('2021-05-28')
    #start vaccinating 18+
    tti_day_vac7= sim.day('2021-07-10')

    s_prob_april = 0.009
    s_prob_may   = 0.012
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.03769
    tn = 0.09
    s_prob_sep = 0.08769
    s_prob_oct = 0.08769
    s_prob_nov = 0.08769
    s_prob_dec = 0.08769
    s_prob_jan = 0.08769
    
    #0.114=70%; 0.149=80%; 0.205=90%

    if future_symp_test is None: future_symp_test = 0.12
    t_delay       = 1.0

    #isolation may-july
    iso_vals = [{k:0.1 for k in 'hswc'}]
    #isolation august
    iso_vals1 = [{k:0.7 for k in 'hswc'}]
    #isolation september
    iso_vals2 = [{k:0.7 for k in 'hswc'}]
    #isolation october
    iso_vals3 = [{k:0.7 for k in 'hswc'}]
    #isolation november
    iso_vals4 = [{k:0.7 for k in 'hswc'}]
     #isolation december
    iso_vals5 = [{k:0.7 for k in 'hswc'}]
    #isolation January-April
    #iso_vals6 = [{k:0.3 for k in 'hswc'}]


    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_sep, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_sep, end_day=tti_day_oct-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_oct, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_oct, end_day=tti_day_nov-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_nov, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_nov, end_day=tti_day_dec-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_dec, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_dec, end_day=tti_day_jan-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_jan, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_jan, end_day=tti_day_feb-1, test_delay=t_delay),
        cv.test_prob(symp_prob=0.114, asymp_prob=0.012, symp_quar_prob=0.0, start_day=tti_day_feb, end_day=tti_day_march-1, test_delay=t_delay),
        cv.test_prob(symp_prob=0.114, asymp_prob=0.015, symp_quar_prob=0.0, start_day=tti_day_march, end_day=tti_day_april-1, test_delay=t_delay),
        cv.test_prob(symp_prob=0.114, asymp_prob=0.02, symp_quar_prob=0.0, start_day=tti_day_april, test_delay=t_delay),  
        cv.contact_tracing(trace_probs={'h': 1, 's': 0.8, 'w': 0.8, 'c': 0.05},
                           trace_time={'h': 0, 's': 1, 'w': 1, 'c': 2},
                           start_day='2020-06-01', end_day='2022-06-30',
                           quar_period=10),
        #cv.contact_tracing(trace_probs={'h': 1, 's': 0.5, 'w': 0.5, 'c': 0.05},
        #                   trace_time={'h': 0, 's': 1, 'w': 1, 'c': 2},
        #                   start_day='2021-03-08',
        #                   quar_period=5),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_august, 'vals': iso_vals1}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_sep, 'vals': iso_vals2}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_oct, 'vals': iso_vals3}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_nov, 'vals': iso_vals4}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_dec, 'vals': iso_vals5}})]
        #cv.dynamic_pars({'rel_death_prob': {'days': tti_day_vac, 'vals': 0.9}})]
        #cv.vaccine(days=[0,14], rel_sus=0.4, rel_symp=0.2, cumulative=[0.7, 0.3])]   
    
        
    
    # vaccination interventions

    # vaccinating 75-100 years old
    interventions += [utils.two_dose_daily_delayed(380e3, start_day=tti_day_vac1, dose_delay=14, delay=8*7,
                                                   take_prob=1.0, rel_symp=0.05,
                                                   rel_trans=0.5, cumulative=[0.7, 1.0], dose_priority=[1.3, 0.2],
                                                   priority_days=[tti_day_vac1, tti_day_vac2, tti_day_vac3, tti_day_vac4, tti_day_vac5, tti_day_vac6], age_priority=[75, 60, 50, 40, 30, 20])]
    # # vaccinating 50-65 years old
    # interventions += [utils.two_dose_daily_delayed(300e3, start_day=tti_day_vac2, dose_delay=21, delay=12*7,
    #                                                take_prob=1.0, rel_symp=0.05,
    #                                                rel_trans=0.5, cumulative=[0.7, 1.0], dose_priority=[1, 0.1],
    #                                                priority_days=[tti_day_vac2, tti_day_vac3], age_priority=[50,40])]
    #vaccinating 18-50 years old
    #interventions += [utils.two_dose_daily_delayed(300e3, start_day=tti_day_vac3, dose_delay=21, delay=7*7,
    #                                               take_prob=1.0, rel_symp=0.05,
    #                                               rel_trans=0.5, cumulative=[0.7, 1.0], dose_priority=[1, 0.1],
    #                                               priority_days=[tti_day_vac3, tti_day_vac4], age_priority=[50,18])]

    
    
    analyzers = []
    analyzers +=  [utils.record_dose_flows(vacc_class=utils.two_dose_daily_delayed)]
    analyzers +=  [cv.age_histogram(datafile='uk_stats_by_age.xlsx', edges=np.concatenate([np.linspace(0, 90, 19),np.array([100])]))]
        



# Finally, update the parameters
    sim.update_pars(interventions=interventions, analyzers=analyzers)

    # Change death and critical probabilities
#    interventions += [cv.dynamic_pars({'rel_death_prob':{'days':sim.day('2020-07-01'), 'vals':0.6}})]


    # Finally, update the parameters
    #sim.update_pars(interventions=interventions)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    sim.initialize()

    return sim


########################################################################
# Run calibration and scenarios
########################################################################
if __name__ == '__main__':

    #betas = [i / 10000 for i in range(72, 77, 1)]

    # Quick calibration
    if whattorun=='quickfit':
        s0 = make_sim(seed=1, beta=0.0078, end_day='2021-05-30', verbose=0.1)
        sims = []
        for seed in range(30):
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sim.label = f"Sim {seed}"
            sims.append(sim)
        msim = cv.MultiSim(sims)
        msim.run()
        #msim.reduce()
        msim.reduce(quantiles = [0.25,0.75]) 
        #sim.to_excel('my-sim.xlsx')
        if do_plot:
            msim.plot(to_plot=to_plot, do_save=True, do_show=False, fig_path=f'uk.png',
                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=60, n_cols=2)

    # Run scenarios
    elif whattorun=='scens':

        #scenarios = ['Roadmap_All', 'Roadmap_Stage2', 'Roadmap_Stage3']
        scenarios = ['Roadmap_All']
        #scenarios = ['FNL', 'fullPNL', 'primaryPNL']
        T = sc.tic()
        for scenname in scenarios:

            print('---------------\n')
            print(f'Beginning scenario: {scenname}')
            print('---------------\n')
            sc.blank()
            s0 = make_sim(seed=1, beta=0.0078, end_day='2021-12-31', calibration=False, scenario=scenname, verbose=0.1)
            #s0.run(until='2021-01-25')
            sims = []

            for seed in range(30):
                sim = s0.copy()
                sim['rand_seed'] = seed
                sim.set_seed()
                sim.label = f"Sim {seed}"
                sims.append(sim)
            msim = cv.MultiSim(sims)
            msim.run(n_cpus=4)
           # msim.run(keep_people=keep_people)
            msim.reduce(quantiles=[0.25, 0.75])

            if save_sim:
                    msim.reduce(quantiles=[0.25, 0.75])
                    msim.save(f'{resfolder}/uk_sim_{scenname}.obj',keep_people=True)
                    #msim.save(f'{resfolder}/uk_sim_{scenname}.obj',keep_people=False)
            if do_plot:
                msim.reduce(quantiles=[0.25, 0.75])
                msim.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path=f'uk_{scenname}_current.png',
                          legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=120, n_cols=2)

            print(f'... completed scenario: {scenname}')
            sc.toc(T) 
    # Devel scenario
    elif whattorun == 'devel':
        s0 = make_sim(seed=1, beta=0.0078, end_day=data_end, verbose=0.1)
        s0.run()
        s0.plot(to_plot=to_plot)
        # s0.save('devel.sim', keep_people=True)
        
    

# Add histogram
if plot_hist:

    aggregate = False

    agehists = []
    for s,sim in enumerate(msim.sims):
        agehist = sim['analyzers'][1]
        if s == 0:
            age_data = agehist.data
        agehists.append(agehist.hists[-1])
    raw_x = age_data['age'].values
    raw_deaths = age_data['cum_deaths'].values
    raw_pos = age_data['cum_diagnoses'].values

    if aggregate:
        x = ["0-29", "30-64", "65-79", "80+"]
        deaths = [raw_deaths[0:6].sum(), raw_deaths[6:13].sum(), raw_deaths[13:16].sum(), raw_deaths[16:].sum()]
        pos = [raw_pos[0:6].sum(), raw_pos[6:13].sum(), raw_pos[13:16].sum(), raw_pos[16:].sum()]
    else:
        x = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85-89", "90+"] #["0-29", "30-54", "55+"]
        deaths = raw_deaths
        pos = raw_pos

    # From the model
    mposlist, mdeathlist = [], []
    for hists in agehists:
        mposlist.append(hists['diagnosed'])
        mdeathlist.append(hists['dead'])
    mdeatharr = np.array(mdeathlist)
    mposarr = np.array(mposlist)
    low_q = 0.1
    high_q = 0.9
    raw_mdbest = pl.mean(mdeatharr, axis=0)
    raw_mdlow  = pl.quantile(mdeatharr, q=low_q, axis=0)
    raw_mdhigh = pl.quantile(mdeatharr, q=high_q, axis=0)
    raw_mpbest = pl.mean(mposarr, axis=0)
    raw_mplow  = pl.quantile(mposarr, q=low_q, axis=0)
    raw_mphigh = pl.quantile(mposarr, q=high_q, axis=0)

    if aggregate:
        mpbest = [raw_mpbest[0:6].sum(), raw_mpbest[6:13].sum(), raw_mpbest[13:16].sum(), raw_mpbest[16:].sum()]
        mplow = [raw_mplow[0:6].sum(), raw_mplow[6:13].sum(), raw_mplow[13:16].sum(), raw_mplow[16:].sum()]
        mphigh = [raw_mphigh[0:6].sum(), raw_mphigh[6:13].sum(), raw_mphigh[13:16].sum(), raw_mphigh[16:].sum()]
        mdbest = [raw_mdbest[0:6].sum(), raw_mdbest[6:13].sum(), raw_mdbest[13:16].sum(), raw_mdbest[16:].sum()]
        mdlow = [raw_mdlow[0:6].sum(), raw_mdlow[6:13].sum(), raw_mdlow[13:16].sum(), raw_mdlow[16:].sum()]
        mdhigh = [raw_mdhigh[0:6].sum(), raw_mdhigh[6:13].sum(), raw_mdhigh[13:16].sum(), raw_mdhigh[16:].sum()]
    else:
        mdbest = raw_mdbest
        mdlow = raw_mdlow
        mdhigh = raw_mdhigh
        mpbest = raw_mpbest
        mplow = raw_mplow
        mphigh = raw_mphigh

    # Plotting
    font_size = 20
    font_family = 'Libertinus Sans'
    pl.rcParams['font.size'] = font_size
    pl.rcParams['font.family'] = font_family
    pl.figure(figsize=(24, 8))
    w = 0.4
    off = .8
    ax = {}
    xl, xm, xr, yb, yt = 0.07, 0.07, 0.01, 0.07, 0.01
    dx = (1-(xl+xm+xr))/2
    dy = 1-(yb+yt)
    X = np.arange(len(x))
    XX = X+w-off

    # Diagnoses
    ax[0] = pl.axes([xl, yb, dx, dy])
    c1 = [0.3,0.3,0.6] # diags
    c2 = [0.6,0.7,0.9] #diags
    pl.bar(X, pos, width=w, label='Data', facecolor=c1)
    pl.bar(XX, mpbest, width=w, label='Model', facecolor=c2)
    for i,ix in enumerate(XX):
        pl.plot([ix,ix], [mplow[i], mphigh[i]], c='k')
    ax[0].set_xticks((X+XX)/2)
    ax[0].set_xticklabels(x)
    pl.xlabel('Age')
    pl.ylabel('Diagnoses')
    sc.boxoff(ax[0])
    pl.legend(frameon=False, bbox_to_anchor=(0.3,0.7))

    # Deaths
    ax[1] = pl.axes([xl+dx+xm, yb, dx, dy])
    c1 = [0.5, 0.0, 0.0] # deaths
    c2 = [0.9, 0.4, 0.3] # deaths
    pl.bar(X, deaths, width=w, label='Data', facecolor=c1)
    pl.bar(XX, mdbest, width=w, label='Model', facecolor=c2)
    for i,ix in enumerate(XX):
        pl.plot([ix,ix], [mdlow[i], mdhigh[i]], c='k')
    ax[1].set_xticks((X+XX)/2)
    ax[1].set_xticklabels(x)
    pl.xlabel('Age')
    pl.ylabel('Deaths')
    sc.boxoff(ax[1])
    pl.legend(frameon=False, bbox_to_anchor=(0.3,0.7))
    
    plotname = 'uk_stats_by_age_agg.png' if aggregate else 'uk_stats_by_age.png'
    cv.savefig(plotname, dpi=100)
    

