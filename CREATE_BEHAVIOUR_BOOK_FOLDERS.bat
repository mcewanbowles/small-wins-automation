@echo off
echo ============================================================
echo   Small Wins Studio - Creating New Book Theme Folders
echo   (Back-to-School / Behaviour line)
echo ============================================================
echo.

set BASE=D:\Seagate\small-wins-automation\assets\themes

REM ── Previously queued (no folder existed yet) ──────────────────
mkdir "%BASE%\personal_space_camp"
mkdir "%BASE%\decibella"
mkdir "%BASE%\what_if_everybody_did_that"
mkdir "%BASE%\have_you_filled_a_bucket_today"
mkdir "%BASE%\the_rabbit_listened"
mkdir "%BASE%\you_get_what_you_get"
mkdir "%BASE%\schools_first_day_of_school"
mkdir "%BASE%\how_full_is_your_bucket"
mkdir "%BASE%\listen_buddy"
mkdir "%BASE%\too_much_glue"
mkdir "%BASE%\do_unto_otters"
mkdir "%BASE%\the_invisible_string"
mkdir "%BASE%\the_magical_yet"

REM ── New titles found this session ───────────────────────────────
mkdir "%BASE%\take_a_kiss_to_school"
mkdir "%BASE%\lola_goes_to_school"
mkdir "%BASE%\kindergarten_where_kindness_matters_every_day"
mkdir "%BASE%\monkey_not_ready_for_kindergarten"
mkdir "%BASE%\youre_wearing_that_to_school"
mkdir "%BASE%\a_bad_case_of_stripes"
mkdir "%BASE%\i_will_be_fierce"
mkdir "%BASE%\butterflies_on_the_first_day_of_school"
mkdir "%BASE%\how_to_get_your_octopus_to_school"
mkdir "%BASE%\school_bus"
mkdir "%BASE%\the_little_school_bus"
mkdir "%BASE%\the_class"
mkdir "%BASE%\this_is_how_we_do_it"
mkdir "%BASE%\how_to_get_your_teacher_ready"
mkdir "%BASE%\the_name_jar"
mkdir "%BASE%\your_name_is_a_song"
mkdir "%BASE%\the_proudest_blue"
mkdir "%BASE%\a_letter_to_my_teacher"
mkdir "%BASE%\if_i_built_a_school"
mkdir "%BASE%\worry_says_what"
mkdir "%BASE%\silly_billy"
mkdir "%BASE%\the_worry_box"
mkdir "%BASE%\hannah_and_sugar"
mkdir "%BASE%\willows_whispers"
mkdir "%BASE%\the_girl_who_never_made_mistakes"
mkdir "%BASE%\saturday_is_swimming_day"
mkdir "%BASE%\when_i_was_a_child_i_was_never_afraid"

REM ── Create activity_images subfolder in each ─────────────────
for %%F in (personal_space_camp decibella what_if_everybody_did_that have_you_filled_a_bucket_today the_rabbit_listened you_get_what_you_get schools_first_day_of_school how_full_is_your_bucket listen_buddy too_much_glue do_unto_otters the_invisible_string the_magical_yet take_a_kiss_to_school lola_goes_to_school kindergarten_where_kindness_matters_every_day monkey_not_ready_for_kindergarten youre_wearing_that_to_school a_bad_case_of_stripes i_will_be_fierce butterflies_on_the_first_day_of_school how_to_get_your_octopus_to_school school_bus the_little_school_bus the_class this_is_how_we_do_it how_to_get_your_teacher_ready the_name_jar your_name_is_a_song the_proudest_blue a_letter_to_my_teacher if_i_built_a_school worry_says_what silly_billy the_worry_box hannah_and_sugar willows_whispers the_girl_who_never_made_mistakes saturday_is_swimming_day when_i_was_a_child_i_was_never_afraid) do (
    mkdir "%BASE%\%%F\activity_images" 2>nul
)

echo.
echo ============================================================
echo   DONE! New book folders created under:
echo   %BASE%
echo ============================================================
echo.
pause
