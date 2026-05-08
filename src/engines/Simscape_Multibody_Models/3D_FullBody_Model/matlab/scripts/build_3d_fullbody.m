function info = build_3d_fullbody(opts)
%BUILD_3D_FULLBODY  One-call build of the 3D_FullBody Simscape model.
%
%   INFO = BUILD_3D_FULLBODY() loads the existing
%   ``GolfSwing3D_Kinetic.slx`` from the sibling ``3D_Golf_Model`` tree,
%   saves a copy as ``GolfSwing3D_FullBody.slx`` next to this build
%   script's model directory, then calls (in order)::
%
%       prune_redundant_logging   — disable redundant signal logging,
%                                    freeing ~30-40 nonvirtual blocks
%                                    (issue #4382 audit).
%       add_leg_chain             — add two legs (hip gimbal, knee
%                                    revolute, ankle universal) and a
%                                    pair of foot/ground contact forces.
%       validate_3d_fullbody      — block count, signal count, smoke
%                                    sim.
%
%   INFO is a struct of build metadata (timestamps, block deltas, etc.)
%   for the caller to inspect or write to a build log.
%
%   BUILD_3D_FULLBODY(OPTS) accepts a struct with optional fields:
%
%       .source_slx           full path to the source model.  Default:
%                             autodetected from the sibling
%                             ``3D_Golf_Model`` tree.
%       .target_slx           full path to write the new model to.
%                             Default: ``../../src/model/GolfSwing3D_FullBody.slx``.
%       .skip_prune           true to skip prune_redundant_logging.
%       .skip_legs            true to skip add_leg_chain.
%       .skip_validate        true to skip validate_3d_fullbody.
%       .report_dir           generated JSON report directory.
%       .build_report_path    build report JSON path.
%       .logging_audit_report_path
%                             prune audit JSON path.
%       .validation_report_path
%                             validation report JSON path.
%       .validation_phase     validation gate phase: scaffold, one_leg,
%                             or full_contact. Default scaffold.
%       .block_budget         Home-license nonvirtual block budget.
%                             Default 1000.
%       .warning_budget       nonvirtual block warning threshold.
%                             Default 900.
%       .verbose              default true.
%
%   Preconditions:
%       - MATLAB R2025b with Simscape Multibody installed.
%       - The source model loads cleanly (call ``load_system`` first
%         to verify).
%
%   Postconditions:
%       - The target ``.slx`` exists, loads, and (when validate is on)
%         simulates for opts.smoke_time without errors.
%
%   See also: PRUNE_REDUNDANT_LOGGING, ADD_LEG_CHAIN, VALIDATE_3D_FULLBODY.

    arguments
        opts (1,1) struct = struct()
    end

    opts = local_fill_defaults(opts);
    info = struct( ...
        'schema_version',  "3d_fullbody_build_report.v1", ...
        'started_at',     datetime('now'), ...
        'source_slx',     string(opts.source_slx), ...
        'target_slx',     string(opts.target_slx), ...
        'artifact_policy', "generated_only_ignored_by_git", ...
        'report_paths',   struct( ...
            'build_report',      string(opts.build_report_path), ...
            'logging_audit',     string(opts.logging_audit_report_path), ...
            'validation_report', string(opts.validation_report_path)), ...
        'phases',         struct(), ...
        'errors',         strings(0,1));

    if opts.verbose
        fprintf('=== build_3d_fullbody ===\n');
        fprintf('  source: %s\n', opts.source_slx);
        fprintf('  target: %s\n', opts.target_slx);
    end

    % --- Phase 0: copy source -> target -------------------------------
    if opts.verbose; fprintf('Phase 0: copying source -> target...\n'); end
    t0 = tic;
    info.phases.copy = local_copy_phase(opts);
    info.phases.copy.elapsed_s = toc(t0);
    if opts.verbose
        fprintf('  copy done in %.1fs (block count: %d)\n', ...
                info.phases.copy.elapsed_s, info.phases.copy.block_count);
    end

    % --- Phase 1: prune redundant logging ----------------------------
    if opts.skip_prune
        if opts.verbose; fprintf('Phase 1: SKIPPED (opts.skip_prune)\n'); end
    else
        if opts.verbose; fprintf('Phase 1: prune_redundant_logging...\n'); end
        t0 = tic;
        info.phases.prune = prune_redundant_logging(opts.target_model_name, ...
            struct('verbose', opts.verbose, ...
                   'audit_report_path', opts.logging_audit_report_path, ...
                   'source_model_path', opts.source_slx, ...
                   'target_model_path', opts.target_slx));
        info.phases.prune.elapsed_s = toc(t0);
        if opts.verbose
            fprintf('  pruned %d signal(s); heuristic savings %d nonvirtual block(s) in %.1fs\n', ...
                info.phases.prune.signals_disabled, ...
                info.phases.prune.blocks_removed, ...
                info.phases.prune.elapsed_s);
        end
    end

    % --- Phase 2: add legs + ground contact --------------------------
    if opts.skip_legs
        if opts.verbose; fprintf('Phase 2: SKIPPED (opts.skip_legs)\n'); end
    else
        if opts.verbose; fprintf('Phase 2: add_leg_chain...\n'); end
        t0 = tic;
        info.phases.legs = add_leg_chain(opts.target_model_name, ...
            struct('verbose', opts.verbose));
        info.phases.legs.elapsed_s = toc(t0);
        if opts.verbose
            fprintf('  added %d block(s) in %.1fs\n', ...
                info.phases.legs.blocks_added, info.phases.legs.elapsed_s);
        end
    end

    % --- Save the modified model -------------------------------------
    if opts.verbose; fprintf('Saving %s...\n', opts.target_slx); end
    save_system(opts.target_model_name, opts.target_slx);

    % --- Phase 3: validate -------------------------------------------
    if opts.skip_validate
        if opts.verbose; fprintf('Phase 3: SKIPPED (opts.skip_validate)\n'); end
    else
        if opts.verbose; fprintf('Phase 3: validate_3d_fullbody...\n'); end
        t0 = tic;
        info.phases.validate = validate_3d_fullbody(opts.target_model_name, ...
            struct('verbose', opts.verbose, ...
                   'smoke_time', opts.smoke_time, ...
                   'phase', opts.validation_phase, ...
                   'budget', opts.block_budget, ...
                   'warning_budget', opts.warning_budget, ...
                   'report_path', opts.validation_report_path, ...
                   'source_model_path', opts.source_slx, ...
                   'target_model_path', opts.target_slx));
        info.phases.validate.elapsed_s = toc(t0);
        if opts.verbose
            fprintf('  validation: %s (%.1fs)\n', ...
                ternary(info.phases.validate.passed, 'PASS', 'FAIL'), ...
                info.phases.validate.elapsed_s);
        end
    end

    info.finished_at = datetime('now');
    info.elapsed_s   = seconds(info.finished_at - info.started_at);
    local_write_build_report(opts.build_report_path, info);
    if opts.verbose
        fprintf('=== build_3d_fullbody complete in %.1fs ===\n', info.elapsed_s);
        fprintf('  build_report_path = %s\n', opts.build_report_path);
    end
end


% =====================================================================
function opts = local_fill_defaults(opts)
%LOCAL_FILL_DEFAULTS  Fill in default values for unset OPTS fields.

    here = fileparts(mfilename('fullpath'));
    fullbody_root = fileparts(fileparts(fileparts(here)));
    repo_root     = fileparts(fileparts(fileparts(fullbody_root)));

    if ~isfield(opts, 'source_slx') || strlength(string(opts.source_slx)) == 0
        opts.source_slx = fullfile(repo_root, ...
            'src', 'engines', 'Simscape_Multibody_Models', '3D_Golf_Model', ...
            'matlab', 'src', 'model', 'GolfSwing3D_Kinetic.slx');
    end
    opts.source_slx = char(opts.source_slx);
    if ~isfile(opts.source_slx)
        error('build_3d_fullbody:noSourceSlx', ...
              'Source model not found: %s', opts.source_slx);
    end

    if ~isfield(opts, 'target_slx') || strlength(string(opts.target_slx)) == 0
        opts.target_slx = fullfile(fullbody_root, ...
            'matlab', 'src', 'model', 'GolfSwing3D_FullBody.slx');
    end
    opts.target_slx = char(opts.target_slx);
    target_dir = fileparts(opts.target_slx);
    if ~isfolder(target_dir); mkdir(target_dir); end

    [~, name, ~] = fileparts(opts.target_slx);
    opts.target_model_name = name;

    if ~isfield(opts, 'skip_prune');    opts.skip_prune    = false; end
    if ~isfield(opts, 'skip_legs');     opts.skip_legs     = false; end
    if ~isfield(opts, 'skip_validate'); opts.skip_validate = false; end
    if ~isfield(opts, 'verbose');       opts.verbose       = true;  end
    if ~isfield(opts, 'smoke_time');    opts.smoke_time    = 0.005; end
    if ~isfield(opts, 'validation_phase') || strlength(string(opts.validation_phase)) == 0
        opts.validation_phase = "scaffold";
    end
    if ~isfield(opts, 'block_budget');   opts.block_budget   = 1000; end
    if ~isfield(opts, 'warning_budget'); opts.warning_budget = 900;  end

    if ~isfield(opts, 'report_dir') || strlength(string(opts.report_dir)) == 0
        opts.report_dir = fullfile(fullbody_root, 'matlab', 'output');
    end
    opts.report_dir = char(opts.report_dir);
    if ~isfolder(opts.report_dir); mkdir(opts.report_dir); end

    if ~isfield(opts, 'build_report_path') || ...
            strlength(string(opts.build_report_path)) == 0
        opts.build_report_path = fullfile(opts.report_dir, 'build_report.json');
    end
    opts.build_report_path = char(opts.build_report_path);

    if ~isfield(opts, 'logging_audit_report_path') || ...
            strlength(string(opts.logging_audit_report_path)) == 0
        opts.logging_audit_report_path = fullfile(opts.report_dir, 'logging_audit.json');
    end
    opts.logging_audit_report_path = char(opts.logging_audit_report_path);

    if ~isfield(opts, 'validation_report_path') || ...
            strlength(string(opts.validation_report_path)) == 0
        opts.validation_report_path = fullfile(opts.report_dir, 'validation_report.json');
    end
    opts.validation_report_path = char(opts.validation_report_path);
end


% =====================================================================
function out = local_copy_phase(opts)
%LOCAL_COPY_PHASE  Copy the source model to the target path.
%
%   We do NOT use a plain file copy because the resulting .slx would
%   carry its OLD model name in its internal metadata.  Instead we
%   load the source, then ``save_system`` to the target path with the
%   new model name — Simulink renames the model identifier to match.
    [~, source_name, ~] = fileparts(opts.source_slx);
    if bdIsLoaded(opts.target_model_name)
        close_system(opts.target_model_name, 0);
    end
    if ~bdIsLoaded(source_name)
        load_system(opts.source_slx);
    end
    save_system(source_name, opts.target_slx, 'OverwriteIfChangedOnDisk', true);
    % Close the source so we don't accidentally edit it.
    close_system(source_name, 0);
    % Re-open the target so subsequent phases mutate it in place.
    load_system(opts.target_slx);
    out = struct( ...
        'source_name', string(source_name), ...
        'target_name', string(opts.target_model_name), ...
        'block_count', local_count_blocks(opts.target_model_name));
end


function n = local_count_blocks(model_name)
%LOCAL_COUNT_BLOCKS  Return total block count (incl. virtual) of MODEL_NAME.
    blocks = find_system(model_name, 'LookUnderMasks', 'all', ...
                                       'FollowLinks',    'on', ...
                                       'Type',           'block');
    n = numel(blocks);
end


function out = ternary(cond, a, b)
    if cond; out = a; else; out = b; end
end


function local_write_build_report(path, info)
%LOCAL_WRITE_BUILD_REPORT  Emit a JSON-safe build report.
    report = struct( ...
        'schema_version', info.schema_version, ...
        'generated_at', string(datetime('now')), ...
        'started_at', string(info.started_at), ...
        'finished_at', string(info.finished_at), ...
        'elapsed_s', double(info.elapsed_s), ...
        'source_slx', info.source_slx, ...
        'target_slx', info.target_slx, ...
        'artifact_policy', info.artifact_policy, ...
        'report_paths', info.report_paths, ...
        'phases', info.phases, ...
        'errors', info.errors);
    local_write_json(path, report);
end


function local_write_json(path, payload)
    path = char(path);
    folder = fileparts(path);
    if strlength(string(folder)) > 0 && ~isfolder(folder)
        mkdir(folder);
    end
    fid = fopen(path, 'w');
    if fid < 0
        error('build_3d_fullbody:reportOpenFailed', ...
              'Could not open report for writing: %s', path);
    end
    cleaner = onCleanup(@() fclose(fid));
    fprintf(fid, '%s\n', jsonencode(payload, 'PrettyPrint', true));
    clear cleaner
end
