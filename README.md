# dcc-scripts
Project IDA DCC Scripts

## Some old notes

-------------------------
### dealing withdraw database (IDA.withdraw)
-------------------------
add_withdraw	- adding records
    add_rec	- 
mod_withdraw	- modifying end time
trans_withdraw	- translating epoch time to human time (info only)
VI_withdraw	- modifying database with vi (if necessary)

-------------------------
### converting raw to Q data:
-------------------------
run.r2q		- daily cron job, calls r2q_proc
r2q_proc	- processing data
    r2q_dataseg	-
    gz_chk_raw	- 
r2q_view	- reviewing data
r2q_send	- sending data to DMC
r2q_sync	- sending sync information to DMC (weekly cron job)

-------------------------
### checking gz files in /ida/stage
-------------------------
gz_check	- daily cron job to check gz files in /ida/stage
    gz_gap	-
gz_mv		- force files to be moved/deleted from /ida/stage

-------------------------
### getting gz file names
-------------------------
GET_GZ_NAME.scr


.....................................................................
check_Parrivals
check_surfacewaves
get_caldata
get_mustang_data
go_plot_big_quakes
go_plot_quakes
plot_cleanup
run_html
run_plot_mustang
run_up_example
russian_adhoc
russian_rename
