# SPA_toolbox test

## Background info

### Description
Currently the SPA_toolbox test are mixed it all over the place. I would like to add some standardisation to the testing.

### Codebase and usage factors
This repo has many tools. Some are uses and developed on their own others are developed together.

### Sometimes I will want to just run one set of test for a specific feature. Sometimes this will be a single test file other times it will be multiple.

### Current I have a script called ZZ_test-RUNNER.py I use this in another repo and like it.

## TASKs

1. Create a mission file called MF-testing-process.md
2. Think about pytest and industry standards of its usage.
   - I don't mind going my own way if it works better for me and my workflow, but I believe sticking to Pythonic practices and industry standard workflows will help develop my skills and create better code.
3. Think about the Background info above and my current usage of test and needs for flexible testing.
4. Write some options of testing workflows. At least 3 options. Include in the option.
   - Brief Description
   - Is it a Pythonic practice, Industry standard workflow or a MACish process. (A MACish is a process I do that is really not a Pythonic practice or Industry standard workflow, but works for me) FYI I don't dev in a team or share or publish my code.
   - Pos and Cons
5. Think of any questions you have for me to clarify my needs, create a better MF-testing-process.md document or help you action this task.

## Clarifying Questions

Before finalizing the mission plan, I need to understand your preferences:

1. **Team/Publishing Context**
   - Will anyone else (now or future) work on this project or use these tests?
   - Do you plan to publish or distribute SPA_toolbox?
   - → *Affects: Option 2/3 more valuable if sharing; Option 1 fine for solo projects*
Publishing - No I don't plan to publish this repo, It's very specific to my needs and task for my role.
Team - No humans other then me, but will be developed and maintain by myself and AI agents.

2. **ZZ_test-RUNNER.py Attachment**
   - How attached are you to the ZZ_test-RUNNER.py as it is?
   - Would you be willing to simplify or retire it if pytest + markers do 90% of it?
   - → *Affects: Option 2 keeps it; Option 3 minimizes it*
I'm not really attached to it. I do want a JSON report of failed tests.

3. **Feature-Based vs. Full-Suite Runs**
   - When you test during development, do you:
     - Usually: Run tests for the feature you're changing (selective)?
     - Or: Run full suite every time (git diff detection is bonus)?
   - → *Affects: All options support selective, but Option 3 makes it easiest*
Both, Usaully I will just run the tests for the changes. But will from time to time run all the test as a repo audit.

4. **Growth Expectations**
   - Do you expect more test files as you add features?
   - Is the codebase relatively stable, or will it grow significantly?
   - → *Affects: Option 1 works now; Option 2/3 scale better*
This repo is the epitome of a dynamic and growing repo.

5. **Skill Building vs. Pragmatism**
   - You mentioned "sticking to Pythonic practices helps me develop skills"
   - How much do you weight: *current efficiency* vs. *long-term skill growth*?
   - → *Affects: Option 1 is fastest; Option 3 is most educational*
Getting the job done is the highist priority. When I get time I will swing back to learn.


pytest tests/test_dog_box/test_ssotsif.py::test_valid_sif tests/test_dog_box/test_ssotsif.py::test_other_test 
work?

Can you do Option B: Wrapper Script (Recommended), but add the ability to give it tests as agrs. EG
`run_tests.py` runs all tests
`run_tests.py -t pytest tests/test_dog_box/test_ssotsif.py::test_valid_sif tests/test_dog_box/test_ssotsif.py::test_other_test tests/test_file_sorter/test_file_identifier.py
 