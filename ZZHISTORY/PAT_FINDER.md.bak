# PAT online Finder

This script will be used to find and move any PATonine files. I should use the SPA_TOOLBOX helper.

1. User will be prompted to select folder or file/s to process and an output folder to move the files to.
2. Finders/PATonline-FINDER.py will process all files by opening the file, finding the cell values Family name and Given name and (Unique ID or Username or both). These could be in any column up to column M and down as far as row 20.
These values could be in any order. Their location and order is not important, the there presents is.

If file only contains Family name, Given name, Username move it to [output_folder]/No_UniqueID/{file_name}
If file only contains Family name, Given name, Unique ID move it to [output_folder]/Only_UniqueID/{file_name}
If file contains Family name, Given name, Unique ID, Username move it [output_folder]/{file_name}

If a file is identified as a PATonline file log it as [INFO], don't log unidentified files.

Do you have any queestions?

OK, use task-planner for this task.
ISSUE
When PATpnline_FINDER.py runs its hard to tell where its at.
Questions
Can we add a progress bar in a window for standalone? What would you recommend for using it as a module? Really it only needs to count the files to be processed and increment for each file processed.