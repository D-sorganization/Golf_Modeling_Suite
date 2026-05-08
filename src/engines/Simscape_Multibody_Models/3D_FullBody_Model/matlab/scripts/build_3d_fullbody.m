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
        'started_at',     datetime('now'), ...
        'source_slx',     string(opts.source_slx), ...
        'target_slx',     string(opts.target_slx), ...
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
            struct('verbose', opts.verbose));
        info.phases.prune.elapsed_s = toc(t0);
        if opts.verbose
            fprintf('  pruned %d signal(s); freed %d nonvirtual block(s) in %.1fs\n', ...
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
                   'smoke_time', opts.smoke_time));
        info.phases.validate.elapsed_s = toc(t0);
        if opts.verbose
            fprintf('  validation: %s (%.1fs)\n', ...
                ternary(info.phases.validate.passed, 'PASS', 'FAIL'), ...
                info.phases.validate.elapsed_s);
        end
    end

    info.finished_at = datetime('now');
    info.elapsed_s   = seconds(info.finished_at - info.started_at);
    if opts.verbose
        fprintf('=== build_3d_fullbody complete in %.1fs ===\n', info.elapsed_s);
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
