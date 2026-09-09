$Base = "D:\Seagate\small-wins-automation\assets\themes"
$FocusFolder = "D:\Seagate\small-wins-automation\assets\themes\_SCHOOL_BEHAVIOUR_FOCUS"

New-Item -ItemType Directory -Force -Path $FocusFolder | Out-Null

$titles = @(
    "first_day_jitters","all_are_welcome","the_day_you_begin","david_goes_to_school",
    "the_kissing_hand","pete_rocking_in_my_school_shoes","we_dont_eat_our_classmates",
    "the_pigeon_has_to_go_to_school","the_recess_queen","stand_tall_molly_lou_melon",
    "chrysanthemum","the_color_monster","interrupting_chicken","pete_school_shoes",
    "time_for_school_little_blue_truck","llama_llama_time_to_share","my_mouth_is_a_volcano",
    "personal_space_camp","decibella","what_if_everybody_did_that",
    "have_you_filled_a_bucket_today","the_rabbit_listened","you_get_what_you_get",
    "schools_first_day_of_school","how_full_is_your_bucket","listen_buddy",
    "too_much_glue","do_unto_otters","the_invisible_string","the_magical_yet",
    "take_a_kiss_to_school","lola_goes_to_school",
    "kindergarten_where_kindness_matters_every_day","monkey_not_ready_for_kindergarten",
    "youre_wearing_that_to_school","a_bad_case_of_stripes","i_will_be_fierce",
    "butterflies_on_the_first_day_of_school","how_to_get_your_octopus_to_school",
    "school_bus","the_little_school_bus","the_class","this_is_how_we_do_it",
    "how_to_get_your_teacher_ready","the_name_jar","your_name_is_a_song",
    "the_proudest_blue","a_letter_to_my_teacher","if_i_built_a_school",
    "worry_says_what","silly_billy","the_worry_box","hannah_and_sugar",
    "willows_whispers","the_girl_who_never_made_mistakes","saturday_is_swimming_day",
    "when_i_was_a_child_i_was_never_afraid"
)

$ws = New-Object -ComObject WScript.Shell
$missing = @()

foreach ($t in $titles) {
    $target = Join-Path $Base $t
    if (Test-Path $target) {
        $shortcutPath = Join-Path $FocusFolder "$t.lnk"
        $shortcut = $ws.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $target
        $shortcut.Save()
    } else {
        $missing += $t
    }
}

Write-Host ""
Write-Host "Done. Shortcuts created in:"
Write-Host $FocusFolder
if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Not found on disk (check spelling / re-run folder creation):"
    $missing | ForEach-Object { Write-Host "  - $_" }
}
