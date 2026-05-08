function out = prune_redundant_logging(model_name, opts)
%PRUNE_REDUNDANT_LOGGING  Disable redundant signal logging in MODEL_NAME.
%
%   OUT = PRUNE_REDUNDANT_LOGGING(MODEL_NAME, OPTS) walks the loaded
%   Simulink model MODEL_NAME and turns off ``LogSimulationData`` /
%   ``SimulationLogging`` on blocks whose output is redundant or
%   non-essential.  The audit in GitHub issue #4382 identified four
%   categories totaling ~33-43 nonvirtual blocks of savings:
%
%     1. Inertia sensors on cosmetic / non-critical solid bodies.
%     2. Per-axis duplicate logs that can be derived from a 3-vector.
%     3. Club force/torque logged in BOTH local and global frames
%        (keep global only).
%     4. Velocity / acceleration logs where position + Δt suffices.
%
%   The defaults below are CONSERVATIVE — they only disable what the
%   audit confirmed is redundant.  Pass OPTS.aggressive=true to also
%   strip the velocity/acceleration mirrors of position channels.
%
%   This function MUTATES the loaded model in place.  Caller must
%   ``save_system`` afterward to persist the changes.
%
%   Args:
%       MODEL_NAME (char/string)  loaded Simulink model name.
%       OPTS (struct)
%         .verbose        default true; print each block touched.
%         .aggressive     default false; also disable vel/acc mirrors.
%         .dry_run        default false; only count, don't toggle.
%
%   Returns:
%       OUT (struct)
%         .signals_disabled   number of LogSimulationData=on flipped to off
%         .blocks_removed     ESTIMATED nonvirtual block reduction
%                             (logged signals consume bus-creator /
%                             outport blocks; ~3 channels per block).
%         .blocks_touched     full list of block paths modified
%         .by_category        per-category breakdown
%
%   See also: BUILD_3D_FULLBODY, ADD_LEG_CHAIN, VALIDATE_3D_FULLBODY.

    arguments
        model_name (1,1) string
        opts (1,1) struct = struct()
    end

    if ~isfield(opts, 'verbose');    opts.verbose    = true;  end
    if ~isfield(opts, 'aggressive'); opts.aggressive = false; end
    if ~isfield(opts, 'dry_run');    opts.dry_run    = false; end

    if ~bdIsLoaded(char(model_name))
        error('prune_redundant_logging:notLoaded', ...
              'Model %s is not loaded.  Call load_system first.', model_name);
    end

    out = struct( ...
        'signals_disabled', 0, ...
        'blocks_removed',   0, ...
        'blocks_touched',   strings(0, 1), ...
        'by_category',      struct( ...
            'cosmetic_solids',    0, ...
            'redundant_axes',     0, ...
            'duplicate_club',     0, ...
            'velocity_mirrors',   0));

    % --- Category 1: Cosmetic / non-critical solid bodies ------------
    % Pattern: any Cylindrical Solid or Brick Solid whose name contains
    % "Cosmetic", "Visual", or known internal-only landmarks.  These
    % carry inertia sensor logs we never read.
    cosmetic_patterns = {'*Cosmetic*', '*Visual*', '*Marker*'};
    out = local_disable_in_blocks(model_name, cosmetic_patterns, ...
        'LogSimulationData', 'cosmetic_solids', opts, out);

    % --- Category 2: Per-axis duplicate position/velocity outputs ----
    % Many Hip/Spine/Torso joints log scalar X, Y, Z outputs separately
    % AND a vector port — disable the scalar mirrors (the consumers
    % all read the vector via CombinedSignalBus).  Pattern: Outport
    % blocks whose name ends in *X, *Y, or *Z and have a sibling vector
    % outport in the same parent.  We use a name-based heuristic
    % matching the audit's enumerated channels.
    redundant_axis_outports = { ...
        'HipPositionInputX',  'HipPositionInputY',  'HipPositionInputZ', ...
        'SpinePositionInputX','SpinePositionInputY', ...
        'LScapPositionInputX','LScapPositionInputY', ...
        'RScapPositionInputX','RScapPositionInputY', ...
        'LSPositionInputX','LSPositionInputY','LSPositionInputZ', ...
        'RSPositionInputX','RSPositionInputY','RSPositionInputZ', ...
        'LWPositionInputX','LWPositionInputY', ...
        'RWPositionInputX','RWPositionInputY'};
    for k = 1:numel(redundant_axis_outports)
        name = redundant_axis_outports{k};
        n = local_disable_outports_by_name(model_name, name, opts);
        out.signals_disabled       = out.signals_disabled + n;
        out.by_category.redundant_axes = out.by_category.redundant_axes + n;
        if n > 0
            out.blocks_touched(end+1, 1) = name;
        end
    end

    % --- Category 3: Club force/torque local-frame duplicates -------
    duplicate_club_outports = { ...
        'ClubLocalForce',       'ClubLocalTorque', ...
        'ClubLocalAngularVel',  'ClubLocalAngularAcc'};
    for k = 1:numel(duplicate_club_outports)
        name = duplicate_club_outports{k};
        n = local_disable_outports_by_name(model_name, name, opts);
        out.signals_disabled         = out.signals_disabled + n;
        out.by_category.duplicate_club = out.by_category.duplicate_club + n;
        if n > 0
            out.blocks_touched(end+1, 1) = name;
        end
    end

    % --- Category 4: Velocity / acceleration mirrors (aggressive only) -
    if opts.aggressive
        vel_acc_outports = { ...
            'HipAngularVelocityX','HipAngularVelocityY','HipAngularVelocityZ', ...
            'HipAngularAccelerationX','HipAngularAccelerationY','HipAngularAccelerationZ', ...
            'TorsoAngularAcceleration', 'SpineAngularAccelerationX', ...
            'SpineAngularAccelerationY'};
        for k = 1:numel(vel_acc_outports)
            name = vel_acc_outports{k};
            n = local_disable_outports_by_name(model_name, name, opts);
            out.signals_disabled            = out.signals_disabled + n;
            out.by_category.velocity_mirrors = out.by_category.velocity_mirrors + n;
            if n > 0
                out.blocks_touched(end+1, 1) = name;
            end
        end
    end

    % Heuristic: each disabled outport / sensor saves on average
    % ~0.7 nonvirtual blocks (because some are Outport blocks (counted)
    % and some are inside SimscapeLogging metadata that doesn't count).
    out.blocks_removed = round(0.7 * out.signals_disabled);

    if opts.verbose
        fprintf('prune_redundant_logging:\n');
        fprintf('  signals_disabled = %d\n', out.signals_disabled);
        fprintf('  blocks_removed (estimate) = %d\n', out.blocks_removed);
        f = fieldnames(out.by_category);
        for i = 1:numel(f)
            fprintf('    %-25s %d\n', f{i}, out.by_category.(f{i}));
        end
    end
end


% =====================================================================
function out = local_disable_in_blocks(model_name, patterns, prop, category, opts, out)
%LOCAL_DISABLE_IN_BLOCKS  Find blocks matching PATTERNS, disable PROP.
%   PATTERNS is a cell array of name globs.  Iterates each pattern,
%   finds matching blocks, and sets PROP to 'off' if currently 'on'.
    for k = 1:numel(patterns)
        try
            blocks = find_system(char(model_name), ...
                'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
                'Type', 'block', 'Name', patterns{k});
        catch
            blocks = {};
        end
        for j = 1:numel(blocks)
            b = blocks{j};
            try
                cur = get_param(b, prop);
            catch
                continue
            end
            if ~strcmpi(cur, 'on'); continue; end
            if ~opts.dry_run
                set_param(b, prop, 'off');
            end
            out.signals_disabled            = out.signals_disabled + 1;
            out.by_category.(category)      = out.by_category.(category) + 1;
            out.blocks_touched(end+1, 1)    = string(b);
            if opts.verbose
                fprintf('  [%s] %s -> %s=off\n', category, b, prop);
            end
        end
    end
end


function n = local_disable_outports_by_name(model_name, outport_name, opts)
%LOCAL_DISABLE_OUTPORTS_BY_NAME  Disable any matching Outport's logging.
%   Outports don't have LogSimulationData; instead we toggle the
%   ``SignalLogging`` property on the line FEEDING the outport, or
%   disable a Test Point if one exists.  Returns the count touched.
    n = 0;
    try
        outports = find_system(char(model_name), ...
            'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
            'BlockType', 'Outport', 'Name', outport_name);
    catch
        outports = {};
    end
    for k = 1:numel(outports)
        b = outports{k};
        % Preferred mechanism: model-level signal logging on the line
        % entering the outport.  Walk up the line and set DataLogging
        % on its source port.
        try
            ph = get_param(b, 'PortHandles');
            line = get_param(ph.Inport(1), 'Line');
            if line > 0
                src_port = get_param(line, 'SrcPortHandle');
                if src_port > 0
                    cur = get_param(src_port, 'DataLogging');
                    if strcmpi(cur, 'on')
                        if ~opts.dry_run
                            set_param(src_port, 'DataLogging', 'off');
                        end
                        n = n + 1;
                        if opts.verbose
                            fprintf('  [redundant_axes] %s -> DataLogging=off\n', b);
                        end
                    end
                end
            end
        catch
            continue
        end
    end
end
